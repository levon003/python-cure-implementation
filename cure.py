# cure.py
# by Freddy Stein and Zach Levonian
# Written as a final project for CS324 - Data Mining
# This file loads the pickled author data and creates clusters from it.

import sys, math
from pickleCreator import *
from kMeansAuthors import *
import itertools

# Percentage of the authors to use in the initial clustering
PRELIM_DATA_PERCENTAGE = 0.15

# Percentage of each preliminary cluster to use as representative points
REPRESENTATIVE_POINTS_PERCENTAGE = 0.005

# Percentage of distance towards cluster centroid each representative point should travel
CENTROID_MIGRATION_PERCENTAGE = 0.20

# Min distance between CURE clusters without merging
CLUSTER_MERGE_DISTANCE = 0.02

# This class describes the conceptual clusters used in the CURE algorithm,
# and contains list to contain the points (Authors) within it as well
# as the representative points.
class CureCluster:
    def __init__(self, id__, center__):
        self.id = id__
        self.authors = []
        self.repPoints = []
        self.center = center__
        
    def __repr__(self):
        return "Cluster #" + str(self.id) + " Size: " + str(len(self.authors))
        
    def addAuthor(self, user):
        self.authors.append(user)
    
    # Computes and stores the centroid of this cluster, based on its authors
    def computeCentroid(self):
        sumPoints = [0 for i in range(6)]
        for author in self.authors:
            addToList(sumPoints, author.getData())
        totalPoints = len(self.authors)
        average = [ sumPoints[i] / totalPoints for i in range(6)]
        self.center = average
    
    # Computes and stores representative points for this cluster, based on its
    # center and the fixed percentage of points to choose.
    def computeRepPoints(self):
        # Choose the first rep point to be the point furthest point from the "center"
        farthestAuthor = None
        farthestDistance = -1
        for author in self.authors:
            dist = clustering.getEucSquaredDistance(author.getData(), self.center)
            if dist > farthestDistance:
                farthestAuthor = author
                farthestDistance = dist
        self.repPoints.append(farthestAuthor.getData())
        numPointsToChoose = int(math.floor(len(self.authors) * REPRESENTATIVE_POINTS_PERCENTAGE))
        # Keep adding points that maximize total distance from each other
        while len(self.repPoints) < numPointsToChoose:
            farthestAuthor = None
            farthestTotalDistance = -1
            for author in self.authors:
                totalDist = 0
                for rep in self.repPoints:
                    totalDist += clustering.getEucSquaredDistance(author.getData(), rep)
                if totalDist > farthestTotalDistance:
                    farthestTotalDistance = totalDist
                    farthestAuthor = author
            self.repPoints.append(farthestAuthor.getData())
    
    # Migrates each representative point a fixed percentage towards
    # the centroid of the cluster
    def moveRepPoints(self):
        for repPoint in self.repPoints:
            for i in range(len(repPoint)):
                distToCenter = math.sqrt((repPoint[i] - self.center[i])**2)
                moveDist = distToCenter * CENTROID_MIGRATION_PERCENTAGE
                if repPoint[i] < self.center[i]:
                    repPoint[i] += moveDist
                elif repPoint[i] > self.center[i]:
                    repPoint[i] -= moveDist
    
    # Merges this cluster with the given clust, recomputing the centroid
    # and the representative points
    def mergeWithCluster(self, clust):
        for author in clust.authors:
            self.addAuthor(author)
        self.computeCentroid()
        self.computeRepPoints()
        self.moveRepPoints()

####

# Coordinates the running of the CURE algorithm, calling the relevant functions
# and ultimately returning the clusters.
# Input: The dictionary of authors, and the number of clusters to create. (authors, k)
# Output: The clusters of authors, as created by the CURE clustering method (clusters)
def runCURE(authors, k):
    print "Standardizing author data."
    authors = standardizeAuthors(authors)
    print "Data standardized. Running preliminary clustering with k=" + str(k) + "."
    prelimClusters, centers, smallAuthors = prelimClustering(k, authors)
    print "Preliminary clustering complete. Building cure clusters."
    clusters = buildCureClusters(prelimClusters, centers, authors, k)
    print "Clusters initialized; choosing representative points."
    clusters = generateRepresentativePoints(clusters)
    print "Representative points chosen. Merging close clusters."
    clusters = mergeCloseClusters(clusters)
    print "Merging complete. " + str(len(clusters)) + " clusters remain."
    print "Assigning remaining data."
    clusters = assignRemainingData(clusters, authors, smallAuthors)
    print "All points assigned. CURE complete."
    return clusters

# Assigns all authors that weren't added via the preliminary clustering
# to an existing cluster based upon the nearest representative point.
# Input: the list of clusters, the dictionary of authors, and the dictionary of authors
#        involved in the initial clustering.
# Output: An updated list of clusters, which now contains all the authors in them. (clusters)
def assignRemainingData(clusters, authors, smallAuthors):
    for authorId in authors:
        if authorId not in smallAuthors:
            clust = getClosestCluster(authors[authorId], clusters)
            clust.addAuthor(authors[authorId])
    return clusters

# Helper function for assignRemainingData()
# Determines the cluster associated with the representative point closest 
# to the given author.
# Input: a given author of class Author, and the list of clusters (author, clusters)
# Output: the clostest cluster for the author, based on repPoints (clustChoice)
def getClosestCluster(author, clusters):
    clustChoice = None
    minDist = 99999
    authorData = author.getData()
    for cluster in clusters:
        for repPoint in cluster.repPoints:
            dist = clustering.getEucSquaredDistance(authorData, repPoint)
            if dist < minDist:
                minDist = dist
                clustChoice = cluster
    return clustChoice
    
# Attempts to merge clusters based on the distance between their closest
# reprsentative points; may result in cluster deletion.
# Input: the list of all the cluster (clusters)
# Output: the list of clusters, which may have had clusters merged together. (clusters)
def mergeCloseClusters(clusters):
    clustersMerged = False
    while clustersMerged:
        for i in range(len(clusters)):
            for j in range(i, len(clusters)):
                closestDist = getClosestClusterDist(clusters[i], clusters[j])
                if closestDist < CLUSTER_MERGE_DISTANCE:
                    clusters[i].mergeWithCluster(clusters[j])
                    del clusters[j]
                    clustersMerged = True
                    break
            if clustersMerged:
                clustersMerged = False
                break
    return clusters

# Helper function for mergeCloseClusters()
# Determines the closest distance between any two representative points for two clusters
# Input: Two clusters of type CureCluster (clust1, clust2)
# Output: the closest distance between any two representative points in the clusters (minDist)
def getClosestClusterDist(clust1, clust2):
    minDist = 9999
    for repPoint1 in clust1.repPoints:
        for repPoint2 in clust2.repPoints:
            dist = clustering.getEucSquaredDistance(repPoint1, repPoint2)
            if dist < minDist:
                minDist = dist
    return minDist

# For each CURE cluster, computes the representative points
# Input: the list of clusters (clusters)
# Output: the list of clusters, but the clusters now have representative points associated
#         with themselves (clusters)
def generateRepresentativePoints(clusters):
    i = 0
    for cluster in clusters:
        cluster.computeRepPoints()
        cluster.moveRepPoints()
        i += 1
        print "  Cluster " + str(i) + " complete."
    return clusters

# Generates initial CURE clusters from the preliminary clusters
# Input: the preliminary Clusters created by k-means, the centers for those clusters,
#        the dictionary of authors, and the number of clusters to create.
#        (prelimClusters, center, authors, k)
# Output: the new list of clusters, which is a list of CureClusters (clusters)
def buildCureClusters(prelimClusters, centers, authors, k):
    clusters = []
    for i in range(k):
        newClust = CureCluster(i, centers[i])
        clusters.append(newClust)
    for id in prelimClusters:
        clusters[prelimClusters[id]].addAuthor(authors[id])
    return clusters

# Performs an initial k-Means clustering on a percentage of the dataset
# to give us some cluster assignments to refine with CURE.
# Input: the number of clusters to create, and the dictionary of authors (k, authors)
# Output: the dictionary of clusters, the centers for those clusters, and the dictionary
#         of authors used to make the initial clusters. (clusters, centers, smallAuthors)
def prelimClustering(k, authors):
    smallAuthors = dict([])
    numEntries = int(math.floor(len(authors) * PRELIM_DATA_PERCENTAGE))
    print "Using " + str(numEntries) + " authors as the preliminary dataset."
    i = 0
    for id in authors:
        smallAuthors[id] = authors[id]
        i += 1
        if i > numEntries:
            break
    print "Computing initial cluster centers."
    initialCenters = getInitialCenters(k, smallAuthors)
    print "Centers chosen. Running kMeans."
    clusters, centers = kMeans(smallAuthors, initialCenters)
    print "kMeans complete; clusters found."
    return clusters, centers, smallAuthors

####

# Given a dictionary of authors, regenerates the orignal values in the feature vector
# Using the original stored value of each feature.
# Input: the dictionary of authors (authors)
# Output: the same dictionary, but with the original values (authors)
def destandardizeAuthors(authors):
    for authorId in authors:
        authors[authorId].buildRepList()
    return authors

# Standardizes each feature by putting it on a 0 to 1 scale
# Actually, fits it on a 0.01-1.01 scale, so we don't need to worry about 0s.
# We chose to standardize in this way because we needed a similar range to 
# account for the huge difference between, for example, the year (1994) and
# the number of journals (2). Log standardization wouldn't account for that.
# http://www.biomedware.com/files/documentation/boundaryseer/Preparing_data/Methods_for_data_standardization.htm
# Input: the dictionary of authors (authors)
# Output: the dictionary of authors, but each author has been standardized via the method
#         described in the link (authors)
def standardizeAuthors(authors):
    maxs, mins = getMaxsAndMins(authors)
    for authorId in authors:
        author = authors[authorId].getData()
        for i in range(len(author)):
            author[i] = (float(author[i] - mins[i]) / (maxs[i] - mins[i]) ) + 0.01
    return authors

# Given a series of clusters of data standardized by the original function,
# finds the original values by reversing the calculation
# Input: the list of CureClusters and the dictionary of authors. (clusters, authors)
# Output: The list of destandardized clusters. Also, authors is destandardized as well.
#         (clusters)
def destandardizeClusterCenters(clusters, authors):
    destandardizeAuthors(authors)
    maxs, mins = getMaxsAndMins(authors)
    for cluster in clusters:
        for i in range(len(cluster.center)):
            cluster.center[i] = ((cluster.center[i] - 0.01) * (maxs[i] - mins[i])) + mins[i]
    return clusters

# Determines the distance from each author to its cluster center. This uses the standardized
# values. Prints both the individual error, and the total error.
# Input: the list of the CureClusters (clusters)
# Output: none, but print the error of the clusters
def determineClustError(clusters):
    j = 1
    aggError = 0
    for cluster in clusters:
        totalDist = 0
        for author in cluster.authors:
            for i in range(len(author.repList)):
                totalDist += math.sqrt((author.repList[i] - cluster.center[i])**2)
        print "Total Clustering Error for Cluster #" + str(j) + ": " + str(totalDist)
        j += 1
        aggError += totalDist
    print "The total Clustering Error for all Clusters is: " + str(aggError)
        

# A helper function which prints the clusters in a way which is readable, and gives
# information about them. Also destandardizes them for readability purposes.
# Input: the list of CureClusters, and the dictionary of authors. (clusters, authors)
# Output: none, but prints information
def printClusters(clusters, authors):
    clusters = destandardizeClusterCenters(clusters, authors)
    i = 1
    for cluster in clusters:
        print "Cluster " + str(i) + ":"
        print "\tCentroid: " + str(cluster.center)
        print "\tNum Authors: " + str(len(cluster.authors))
        i += 1

def main():
    k = 5
    if (len(sys.argv) != 2):
        print "Usage: pypy cure.py k"
        print "Continuing with k = 5"
    else:
        k = int(sys.argv[1])
    print "Attempting to load author data pickle."
    authors = getAuthorsPickle("authorsFull.p")
    # Can also load up authorsSmall.p for a faster runtime
    print str(len(authors)) + " authors in dataset."
    clusters = runCURE(authors, k)
    determineClustError(clusters)
    printClusters(clusters, authors)
    
if __name__ == '__main__':
    main()