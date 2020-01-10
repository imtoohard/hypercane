import logging
import otmt
import lxml.etree
import random
import copy

from justext import justext, get_stoplist
from aiu import convert_LinkTimeMap_to_dict
from requests.exceptions import ConnectionError, TooManyRedirects
from requests.exceptions import RequestException
from requests_futures.sessions import FuturesSession
from simhash import Simhash
from datetime import datetime

module_logger = logging.getLogger('hypercane.reduce.remove_offtopic')

class HypercaneMementoCollectionModel(otmt.CollectionModel):
    
    def __init__(self, dbconn, session):
        """This class assumes session is an instance of CachedSession"""
        
        self.dbconn = dbconn
        self.session = session

        db = self.dbconn.get_default_database()
        self.error_collection = db.mementoerrors
        self.bpfree_collection = db.bpfree
        self.derived_collection = db.derivedvalues

        self.urimlist = []
        self.uritlist = []

    def __del__(self):
        """Override parent destructor."""
        pass

    def addTimeMap(self, urit):
        """Adds a TimeMap to the object, parsing it if it is in link-format
        and then stores the TimeMap as a dict in memory and JSON on disk.
        If JSON is given as `content`, then it is just converted to a dict.
        """
        self.session.get(urit)
        self.uritlist.append(urit)

    def getTimeMap(self, urit):
        """
            Returns the dict form of TimeMap at `urit` provided that it
            was previously stored via `addTimeMap`.
        """
        return convert_LinkTimeMap_to_dict(self.session.get(urit).text)

    def addMemento(self, urim):
        try:
            self.session.get(urim)
            raw_urim = otmt.generate_raw_urim(urim)
            self.session.get(raw_urim)
            self.urimlist.append(urim)
        except (ConnectionError, TooManyRedirects) as e:
            self.addMementoError(urim, bytes(repr(e), "utf8"))

    def addManyMementos(self, urims):

        futuressession = FuturesSession(session=self.session)
        futures = {}

        working_urim_list = []

        for uri in urims:

            raw_urim = otmt.generate_raw_urim(uri)
            working_urim_list.append(uri)
            futures[uri] = futuressession.get(uri)
            futures[raw_urim] = futuressession.get(raw_urim)

        def uri_generator(urilist):

            while len(urilist) > 0:

                uchoice = random.choice(urilist)

                yield uchoice

        for uri in uri_generator(working_urim_list):

            if futures[uri].done():

                try:
                    r = futures[uri].result()
                    if 'memento-datetime' not in r.headers:
                        self.addMementoError(uri, "URI-M {} does not produce a memento".format(uri))
    
                except RequestException as e:
                    self.addMementoError(uri, bytes(repr(e), "utf-8"))
                    continue

                working_urim_list.remove(uri)
                del futures[uri]


    def addMementoError(self, urim, errorinformation):
        """Associates `errorinformation` with memento specified by `urim` to
        the object, `content` and `headers` can also be stored from the given
        input transaction. If there are no headers or content, use content=""
        and headers={}.
        """
        self.error_collection.insert_one(
            {   
                "urim": urim, 
                "error_information": errorinformation
            }
        )

    def getMementoContent(self, urim):
        """Returns the HTTP entity of memento at `urim` provided that it
        was previously stored via `addMemento`.

        If no data was stored via `addMemento` for `urim`, then
        `CollectionModelNoSuchMementoException` is thrown.

        If data was stored via `addMementoError` for `urim`, then
        `CollectionModelMementoErrorException` is thrown.
        """
        raw_urim = otmt.generate_raw_urim(urim)
        return self.session.get(raw_urim).text

    def getMementoErrorInformation(self, urim):
        """Returns the error information associated with `urim`, provided that
        it was previously stored via `addMementoError`.
        If no data was stored via `addMemento` for `urim`, then
        `CollectionModelNoSuchMementoException` is thrown.
        """
        
        result = self.error_collection.find_one(
            { "urim": urim }
        )

        if result is None:
            if urim in self.urimlist:
                return None
        else:
            return result["error_information"]

    def getMementoContentWithoutBoilerplate(self, urim):
        """Returns the HTTP entity of memento at `urim` with all boilerplate
        removed, provided that it was previously stored via `addMemento`.

        If no data was stored via `addMemento` for `urim`, then
        `CollectionModelNoSuchMementoException` is thrown.

        If data was stored via `addMementoError` for `urim`, then
        `CollectionModelMementoErrorException` is thrown.

        If the boilerplate removal process produces an error for `urim`,
        then CollectionModelBoilerPlateRemovalFailureException is thrown.
        """

        if self.getMementoErrorInformation(urim) is not None:
            raise otmt.CollectionModelMementoErrorException(
                "Errors were recorded for URI-M {}".format(urim))

        bprecord = self.bpfree_collection.find_one(
            { "urim": urim }
        )

        if bprecord is not None:
            return bprecord["boilerplate free content"]

        # else...
        try:
            paragraphs = justext(
                self.getMementoContent(urim), get_stoplist('English'))

            content_without_boilerplate = ""
                
            for paragraph in paragraphs:
                content_without_boilerplate += \
                    "{}\n".format(paragraph.text)

            self.bpfree_collection.insert_one(
                {
                    "urim": urim,
                    "boilerplate free content": content_without_boilerplate,
                    "algorithm": "justext"
                }
            )

            return content_without_boilerplate

        except (lxml.etree.ParserError, lxml.etree.XMLSyntaxError) as e:
            raise otmt.collectionmodel.CollectionModelBoilerPlateRemovalFailureException(repr(e))

    def getRawSimhash(self, urim):

        if self.getMementoErrorInformation(urim) is not None:
            raise otmt.CollectionModelMementoErrorException(
                "Errors were recorded for URI-M {}".format(urim))

        derived_record = self.derived_collection.find_one(
            { "urim": urim }
        )

        if derived_record is not None:
            try:
                raw_simhash = derived_record["raw simhash"]
                return raw_simhash
            except KeyError:
                content = self.getMementoContent(urim)
                raw_simhash = Simhash(content).value

                self.derived_collection.update(
                    { "urim": urim },
                    { "$set": { "raw simhash": str(raw_simhash) } }
                )
                return str(raw_simhash)

        else:
            content = self.getMementoContent(urim)
            raw_simhash = Simhash(content).value

            self.derived_collection.insert_one(
                { "urim": urim, "raw simhash": str(raw_simhash) }
            )

        return str(raw_simhash)

    def getFirstURIMByRawSimhash(self, raw_simhash):
        """This function expects getRawSimhash to have been called first."""

        matching_cursor = self.derived_collection.find(
            { "raw simhash": raw_simhash },
            { "urim": 1 }
        )

        matching_cursor.rewind()

        matching_urims = []

        for record in matching_cursor:

            urim = record['urim']

            mdt = datetime.strptime(
                self.getMementoHeaders(urim)['memento-datetime'],
                "%a, %d %b %Y %H:%M:%S GMT"
            )

            matching_urims.append( ( mdt, record["urim"] ) )

        return sorted(matching_urims, reverse=True)[0]


    def getMementoHeaders(self, urim):
        """Returns the headers associated with memento at `urim`.
        """
        return self.session.get(urim).headers

    def getMementoURIList(self):
        """Returns a list of all URI-Ms stored in this object."""
        return self.urimlist

    def getTimeMapURIList(self):
        """Returns a list of all URI-Ts stored in this object."""
        return self.uritlist

def get_list_of_ontopic(measuremodel):

    ontopic_mementos = []

    for urit in measuremodel.get_TimeMap_URIs():
        for urim in measuremodel.get_Memento_URIs_in_TimeMap(urit):

            try:
                if measuremodel.get_overall_off_topic_status(urim) == "on-topic":
                    ontopic_mementos.append(urim)
            except KeyError:
                module_logger.error("failed to get on-topic status for URI-M {}".format(urim))

    return ontopic_mementos

def detect_off_topic(collection_model, timemap_measures, num_topics=None):

    mm = otmt.MeasureModel()

    for measure in timemap_measures:

        module_logger.info("Processing mementos using TimeMap measure {}".format(measure))

        if measure == "gensim_lda" or measure == "gensim_lsi":

            if num_topics is None:
                num_topics = otmt.supported_timemap_measures[measure]["default number of topics"]

            mm = otmt.supported_timemap_measures[measure]["function"](
                collection_model, mm, num_topics=num_topics)

        else:

            mm = otmt.supported_timemap_measures[measure]["function"](
                collection_model, mm)

        module_logger.info("mm: {}".format(mm))

        threshold = timemap_measures[measure]

        mm.calculate_offtopic_by_measure(
            "timemap measures", measure, threshold,
            otmt.supported_timemap_measures[measure]["comparison direction"]
            )

        mm.calculate_overall_offtopic_status()

        ontopic_mementos = get_list_of_ontopic(mm)

        return ontopic_mementos
