# kMeansAuthors.py
# by Zach Levonian and Freddy Stein
# Contains a revised version of kMeans to play nice with the authors' dictionary data structure
# Convenience functions; intended to be used via import

import clustering, random, math

# Runs kMeans on the given authors, returning the clusters
# Input: the dictionary of authors, and the list of intial centers. (authors, centers)
# Output: the dictionary of clusters, and the list of final centers. (clusters, centers)
def kMeans(authors, centers):
    clusters = dict([])
    for id in authors:
        clusters[id] = clustering.getNearestCenter(authors[id].getData(), centers)
    while True:
        prevClusters = clusters.copy()
        
        centers = getNewCenters(authors, clusters, centers)
        
        while True:
            clustTotals = [0 for i in range(len(centers))]
            for id in authors:
                clusters[id] = clustering.getNearestCenter(authors[id].getData(), centers)
                clustTotals[clusters[id]] += 1
            emptyClusts = clustering.getEmptyClusts(clustTotals)
            if len(emptyClusts) > 0:
                #Reposition empty cluster centers and try again
                centers = assignEmptyCenters(authors, centers, emptyClusts)
            else: #No empty clusters detected.
                break
        
        if getClusterShift(prevClusters, clusters) <= 5:
            return clusters, centers

# Returns the amount of shifting between two assignments of points to clusters
# Input: the dictionary of where the authors were last iteration, and where the
#        authors are for the current iteration. (prev, curr)
# Output: the number of shifts which occured. (totalShift)
def getClusterShift(prev, curr):
    totalShift = 0
    for id in prev:
        if prev[id] != curr[id]:
            totalShift += 1
    return totalShift

# Reassigns each empty cluster to its closest author
# Input: the dictionary of authors, the list of centers, and the list of empty clusters
#        (authors, centers, empty)
# Output: a newly updated list of centers, where there are no longer empty clusters. (centers)
def assignEmptyCenters(authors, centers, empty):
    DISTANCE = 0
    ID = 1
    closestPoint = dict([])
    #Initialize the closest point for each empty cluster center to be invalid and VERY far away
    for clustIndex in empty:
        closestPoint[clustIndex] = (999999, -1)
    for id in authors:
        for clustIndex in empty:
            dist = clustering.getEucSquaredDistance(authors[id].getData(), centers[clustIndex])
            if dist < closestPoint[clustIndex][DISTANCE]:
                #Found a closer point; use this id unless we find a better one
                closestPoint[clustIndex] = (dist, id)
    for clustIndex in empty: #Actually assign the location of the new centers
        centers[clustIndex] = authors[id].getData()
    return centers

# Computes the new centers for a cluster given a cluster assignment
# Gets the average of all points assigned to that cluster, or doesn't
# move the cluster if it has no points inside of it.
# Input: the dictionary of authors, the dictionary of clusters, and the list of centers
#        (authors, clusters, centers)
# Output: A list of averages for each cluster, which are then used as new cluster
#         centers. (clustAverages)
def getNewCenters(authors, clusters, centers):
    k = len(centers)
    clustSums = [[0 for j in range(6)] for i in range(k)]
    clustTotals = [0 for i in range(k)]
    for id in authors:
        clustNum = clusters[id]
        clustTotals[clustNum] += 1
        addToList(clustSums[clustNum], authors[id].getData())
    clustAverages = [[0 for j in range(6)] for i in range(k)]
    for i in range(k):
        if clustTotals[i] != 0:
            clustAverages[i] = [clustSums[i][j] / clustTotals[i] for j in range(6)]
    return clustAverages
    
# Convenience method; Adds the vals of list b to the contents of list a
# Input: two lists of equal length (a, b)
# Output: one list, which the addition of the lists (a)
def addToList(a, b):
    if len(a) != len(b):
        return None
    for i in range(len(a)):
        a[i] += b[i]
    return a

# Finds initial cluster centers for kMeans by picking the first point
# at random, then selecting the point that maximiszes distance from all
# previously picked centers.
# Input: the number of clusters to create at first, and the dictionary of authors
#        which had been previously obtained from a pickled file. (k, authors)
# Output: initial cluster centers, which are stored in a list of k size (centers)
def getInitialCenters(k, authors):
    centers = []
    initialPoint = random.choice(authors.keys())
    numFeatures = len(authors[initialPoint].getData())
    centers.append(authors[initialPoint].getData())
    for i in range(k - 1):
        farPoint = []
        maxDist = 0
        for id in authors:
            author = authors[id].getData()
            totalDist = 0
            for center in centers:
                totalDist += clustering.getEucSquaredDistance(author, center)
            if totalDist > maxDist:
                maxDist = totalDist
                farPoint = author
        centers.append(farPoint)
    return centers

# This function finds the max and mins of each of the parameters associated
# with an author.
# Input: the dictionary of all the authors (authors)
# Output: the max value and min value for each author. This is used in standardization
#         (maxs, mins)
def getMaxsAndMins(authors):
    maxs = [0 for i in range(6)]
    mins = [99999 for i in range(6)]
    for authorId in authors:
        author = authors[authorId].getData()
        for i in range(len(author)):
            if author[i] > maxs[i]:
                maxs[i] = author[i]
            if author[i] < mins[i]:
                mins[i] = author[i]
    return maxs, mins
