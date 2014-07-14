# pickleCreator.py - This file creates the pickled dictionary of authors
#   from the various data files; a lot of parsing and handling of bad input happens here.
# by Zachary Levonian and Freddy Stein

import re
import cPickle as pickle

# The filename of the output pickle, which is a dictionary of authors
OUT_FILENAME = "authorsSmall.p"

# These constants limit the number of lines read from the data files.
# Will read in to the nearest 10000th + 1, rounded up.
PAPERAUTHOR_NUM = 1000000
PAPER_NUM = 1000000

# Number of papers an author must have in the dataset to be considered
PAPERS_THRESHOLD = 4

# This class describes a scholarly author in some detail;
# A dictionary of these objects will be pickled to a file for clustering.
class Author:
    def __init__(self, _id, _name):
        self.id = _id
        self.name = _name
        #self.conferences = [] #These are totally unused
        #self.journals = []    #Could add them as a feature: Intersection size between two users.
        self.papers = []
        self.numConferences = 0
        self.numJournals = 0
        self.yearsActive = 0
        self.firstYearPublished = 9999
        self.lastYearPublished = 0
        self.numPapers = 0
        self.repList = []
    
    def __repr__(self):
        selfStr = str(self.id) + " " + self.name + "\n"
        selfStr += "\tNumber of Papers: " + str(len(self.papers)) + "\n"
        selfStr += "\tConferences: " + str(self.numConferences) + "\n"
        selfStr += "\tJournals: " + str(self.numJournals) + "\n"
        selfStr += "\tYears Active: " + str(self.yearsActive) + "\n"
        return selfStr
    
    def __str__(self):
        return self.__repr__()
    
    def addPaper(self, paper):
        self.papers.append(paper)
    
    def hasPaper(self, paper):
        return (paper in self.papers)
        
    def printPapers(self):
        for i in range(len(self.papers)):
            print self.papers[i]
    
    def buildRepList(self):
        self.repList = [self.numPapers, self.numConferences, self.numJournals, \
                       self.yearsActive, self.firstYearPublished, self.lastYearPublished]
    
    def getData(self):
        return self.repList

# This class contains information about an individual paper
class Paper:
    def __init__(self, _id):
        self.id = _id
        self.name = ""
        self.conference = 0
        self.journal = 0
        self.year = 0
        self.authors = []
    
    def addAuthor(self, author):
        self.authors.append(author)
        
    def hasAuthor(self, author):
        return (author in self.authors)

####

# Generic file reading method. Skips the first line, as it assumes it's a header.
# Input: Name of the file to read (fileName)
# Output: the lines of the file which has just been read (data)
def loadData(fileName):
    inFile = open(fileName, 'r')
    inFile.readline()
    data = inFile.readlines()
    inFile.close()
    return data

# Loads in the papers. Then runs through all the papers, and updates the paper
# associated with it if it already exist in the papers set created by
# running through PaperAuthor. This takes some time. If the paper
# has no author attached to it, then it is ignored.
# Input: The dictionary of papers which was previously created by PaperAuthor (papers)
# Output: That dictionary list of papers, which is now updated with information (papers)
def getPaperInfo(papers):
    papersFile = loadData("dataRev2/Paper.csv")
    print "File loaded; parsing lines."
    newPaper = ""
    time = 0
    for paper in papersFile:
        time += 1
        if time % 10000 == 0:
            print "Line: " + str(time)
            if time > PAPER_NUM:
                return papers
        if re.match("\d+,", paper) != None and newPaper != "":
            newPaper = re.sub("\".*\",(?=\d+|-\d+)", ',', newPaper, flags=re.MULTILINE | re.DOTALL)
            content = newPaper.split(",")
            paperId = int(content[0])
            if paperId not in papers:
                newPaper = ""
                newPaper += paper.strip()
                continue
            year = int(content[2])
            conferenceId = int(content[3])
            journalId = int(content[4])
            paperObj = papers[paperId]
            if conferenceId > 0:
                paperObj.conference = conferenceId
            if journalId > 0:
                paperObj.journal = journalId
            if year > 0:
                if year > 2013:
                    year = 2013
                if year < 1960:
                    year = 1960
                paperObj.year = year
            newPaper = ""
        newPaper += paper.strip()
    return papers

# Adds papers associated with at least one author in the given dict
# to a paper dictionary.  Only extracts paper id and author id. This program
# takes quite a while to run, as PaperAuthor is a massive file.
#
# But actually, it takes a really long time to run. Just a warning.
#
# Input: the dictionary of authors previously created by getAuthors() (authors)
# Output: updated authors, who now have papers associated with them, and a 
#         new dictionary of papers, which is every paper which is confirmed to have an author
#         (papers, authors)
def readPaperAuthor(authors):
    papers = dict([])
    lines = loadData("dataRev2/PaperAuthor.csv")
    print "File loaded; parsing lines."
    time = 0
    for line in lines:
        content = line.split(",")
        if len(content) <= 2:
            print "Skipping line " + line
            continue
        paperId = int(content[0])
        authorId = int(content[1])
        if authorId in authors:
            authors[authorId].addPaper(paperId)
            if paperId not in papers:
                paper = Paper(paperId)
                papers[paperId] = paper
            papers[paperId].addAuthor(authorId)
        time += 1
        if (time % 10000) == 0:
        	print "Line:", time
        	if (time > PAPERAUTHOR_NUM):
        		return papers, authors
    return papers, authors

# Returns a dictionary of authors, with only id and name filled
# Input: none
# Output: A dictionary of authors (authors)
def getAuthors():
    authors = dict([])
    lines = loadData("dataRev2/Author.csv")
    for line in lines:
        content = line.split(",")
        authorId = int(content[0])
        authorName = content[1]
        author = Author(authorId, authorName)
        authors[authorId] = author
    return authors

# Calculates the various features from the set of papers associated
# with each author. Further elaborated within the program itself
# Input: the dictionary of authors and the dictionary of papers (authors, papers)
# Output: the newly updated list of authors. Papers is no longer needed (authors)
def recomputeAuthors(authors, papers):
    toDel = []
    for author in authors:
        #First, delete any author from the set that has fewer than t papers
        if len(authors[author].papers) < PAPERS_THRESHOLD:
            toDel.append(author)
            continue
        #Second, compute firstYearPublished and lastYearPublished.
        #Third, compute numConferences and numJournals
        #Fourth, build the conferences and journals lists
        authorObj = authors[author]
        for paperId in authorObj.papers:
            paper = papers[paperId]
            if paper.year != 0:
                if paper.year > authorObj.lastYearPublished:
                    authorObj.lastYearPublished = paper.year
                if paper.year < authorObj.firstYearPublished:
                    authorObj.firstYearPublished = paper.year
            if paper.conference != 0:
                authorObj.numConferences += 1
                #authorObj.conferences.append(paper.conference)
            if paper.journal != 0:
                authorObj.numJournals += 1
                #authorObj.journals.append(paper.journal)
        #Fifth, compute yearsActive, if at least one paper had a year
        if authorObj.lastYearPublished == 0 and authorObj.firstYearPublished == 9999:
            toDel.append(author) #Delete authors without any year info
            continue
        authorObj.yearsActive = authorObj.lastYearPublished - authorObj.firstYearPublished
        #Sixth, confirm the number of papers
        authorObj.numPapers = len(authorObj.papers)
        #Seventh, compute the actual list that will be used in CURE
        authorObj.buildRepList()
    #Complete the deletion
    for key in toDel:
        del authors[key]
    return authors

# Creates the actual pickle file.
# Input: the dictionary of authors to pickle, and the name of the file to place the info in
#        (authors, fileName)
# Output: None
def createPickleFile(authors, fileName):
    pickle.dump(authors, open(fileName, 'wb'))


# Loads the pickle file.
# Input: the filename of the pickled data (file)
# Output: the dictionary of authors which had previously been created (authors)
def getAuthorsPickle(file):
    authors = pickle.load( open( file, "rb" ) )
    print "Pickle loaded."
    return authors

# Loads all the various datafiles, with the intention of creating a dictionary of 
# authors which can be used in a clustering algorithm.
# Input: None
# Output: Creates a pickle file at the designated OUT_FILENAME, and also prints all the
#         authors, which reveals the # of papers published, info about conferences and 
#         journals, and the # of years active.
def main():
    print "Loading authors."
    authors = getAuthors()
    print "Authors loaded."
    print "Starting to read PaperAuthor."
    papers, authors = readPaperAuthor(authors)
    print "Paper-author pairs loaded. Loading paper data."
    papers = getPaperInfo(papers)
    print "Paper info filled. Recomputing author data."
    authors = recomputeAuthors(authors, papers)
    print "Author data recomputed. Creating pickle file."
    createPickleFile(authors, OUT_FILENAME)
    for key in authors:
        print authors[key]
    print len(authors)

if __name__ == '__main__':
    main()

