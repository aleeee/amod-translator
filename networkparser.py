"""
File: networkparser.py

This file takes in an xml file that can be used by MATSim as a network
file and turns it into a dictionary that maps each node to all the neighbors
it can reach.
"""

import xml.etree.ElementTree as ET
import sys
from collections import namedtuple
import numpy as np
import scipy.io as sio

#namedtuple containing link information
link = namedtuple("link", "start finish capacity speed length")
nodetuple = namedtuple("node", "id long lat")

"""
Function: parseNodes
This function takes in the nodes branch of the 
network file and turns it into a list of nodes
to be used as the keys for the dictionary.
"""
def parseNodes(branch):
	nodes = []
	for node in branch:
		nodes.append(nodetuple(node.attrib['id'], node.attrib['x'], node.attrib['y']))
	return nodes

"""
Function: parseLinks
This function takes in a dictionary called graph
which has the nodes as keys and maps all the nodes
to the nodes that can be reached from them.
It also keeps track of all the links and their necessary information.
***NB: nodes are given new ID numbers to make them all from 0...N-1****
instead of the random numbers that they could have been before.
"""
def parseLinks(links, branch, indexer):
	roads = []
	for piece in branch:
		#if lengths are really small, then it makes sense to magnify them by a factor of 1000
		#as it doesn't change the optimization problem
		if float(piece.attrib['length']) < .01 and float(piece.attrib['length']) > 0:
			length = str(float(piece.attrib['length'])*1000)
		else:
			length = piece.attrib['length']
		road = link(piece.attrib['from'], piece.attrib['to'], piece.attrib['capacity'],\
					piece.attrib['freespeed'], length)
		roads.append(road)
		links[indexer[road.start]].append(indexer[road.finish])

	return links, roads

"""
Function: createNodeIndexer
This function creates a dictionary that maps each node to an index
to be used in matrices.
"""
def createNodeIndexer(nodes):
	indexes = [x for x in range(len(nodes))] 
	return dict(((node.id,x) for x,node in zip(indexes,nodes)))

"""
Function: createTravelTimeMatrix
This function creates an nxn matrix that has the following property:
matrix[i][j] is the travel time from node i to node j.
"""
def createTravelTimeMatrix(nodes, links, indexer):
	matrix = np.zeros((len(nodes), len(nodes)))
	for link in links:
		start = indexer[link.start]
		end = indexer[link.finish]
		matrix[start][end] = float(link.length)/float(link.speed)

	return matrix

"""
Function: createCapacityMatrix
This function creates an nxn matrix that has the following property:
matrxix[i][j] is the capacity of the link from i to j.
If the system is capacity symmetric, the matrix will be symmetric as well.
"""
def createCapacityMatrix(nodes, links, indexer):
	matrix = np.zeros((len(nodes), len(nodes)))
	for link in links:
		start = indexer[link.start]
		end = indexer[link.finish]
		matrix[start][end] = link.capacity

	return matrix

"""
Function: createNodeLocationsMatrix
This function takes in a list of nodes and returns an Nx2 matrix
containing the latitudes and longitudes of each node. Note: latitude
comes first in the pairing even though it is the "y" coordinate in the
network.xml files
"""
def createNodeLocationsMatrix(nodes):
	locations = np.zeros((len(nodes), 2))
	for i, node in enumerate(nodes):
		locations[i][0] = node.lat
		locations[i][1] = node.long

	return locations

"""
Function: parseNetwork
This function takes in the name of an xml file that will be converted
into a graph for MATLab to work with.
"""
def parseNetwork(filename):
	tree = ET.parse(filename)
	root = tree.getroot()

	for child in root:
		if child.tag == "nodes":
			nodes = parseNodes(child)
			indexer = createNodeIndexer(nodes)
			graph = dict((node.id,[]) for node in nodes)
		if child.tag == "links":
			links = np.zeros(len(nodes), dtype=object) #empty array which will eventually be converted to cell
			for i in range(len(links)): #initialize each entry to be an empty list
				links[i] = []
			links, roads = parseLinks(links, child, indexer)

	with open('test.txt', 'w') as f:
		for element in links:
			f.write(str(element))
	
	traveltimes = createTravelTimeMatrix(nodes, roads, indexer)
	capacities = createCapacityMatrix(nodes, roads, indexer)
	locations = createNodeLocationsMatrix(nodes)
	
	print(locations)

	#TO DO: Figure out what format the output should be in
	filename = filename[:-4] + ".mat"
	sio.savemat(filename, {'RoadGraph': links, 'CapacityMatrix': capacities, \
						   'TravelTimes': traveltimes, 'Locations': locations})

if __name__ == "__main__":
	parseNetwork(sys.argv[1])