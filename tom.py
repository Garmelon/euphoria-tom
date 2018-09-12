import asyncio
import configparser
import logging
import re

import yaboli
from yaboli.utils import *


ELEMENTS = [
	("H", "Hydrogen"),
	("He", "Helium"),
	("Li", "Lithium"),
	("Be", "Beryllium"),
	("B", "Boron"),
	("C", "Carbon"),
	("N", "Nitrogen"),
	("O", "Oxygen"),
	("F", "Fluorine"),
	("Ne", "Neon"),
	("Na", "Sodium"),
	("Mg", "Magnesium"),
	("Al", "Aluminium"),
	("Si", "Silicon"),
	("P", "Phosphorus"),
	("S", "Sulfur"),
	("Cl", "Chlorine"),
	("Ar", "Argon"),
	("K", "Potassium"),
	("Ca", "Calcium"),
	("Sc", "Scandium"),
	("Ti", "Titanium"),
	("V", "Vanadium"),
	("Cr", "Chromium"),
	("Mn", "Manganese"),
	("Fe", "Iron"),
	("Co", "Cobalt"),
	("Ni", "Nickel"),
	("Cu", "Copper"),
	("Zn", "Zinc"),
	("Ga", "Gallium"),
	("Ge", "Germanium"),
	("As", "Arsenic"),
	("Se", "Selenium"),
	("Br", "Bromine"),
	("Kr", "Krypton"),
	("Rb", "Rubidium"),
	("Sr", "Strontium"),
	("Y", "Yttrium"),
	("Zr", "Zirconium"),
	("Nb", "Niobium"),
	("Mo", "Molybdenum"),
	("Tc", "Technetium"),
	("Ru", "Ruthenium"),
	("Rh", "Rhodium"),
	("Pd", "Palladium"),
	("Ag", "Silver"),
	("Cd", "Cadmium"),
	("In", "Indium"),
	("Sn", "Tin"),
	("Sb", "Antimony"),
	("Te", "Tellurium"),
	("I", "Iodine"),
	("Xe", "Xenon"),
	("Cs", "Caesium"),
	("Ba", "Barium"),
	("La", "Lanthanum"),
	("Ce", "Cerium"),
	("Pr", "Praseodymium"),
	("Nd", "Neodymium"),
	("Pm", "Promethium"),
	("Sm", "Samarium"),
	("Eu", "Europium"),
	("Gd", "Gadolinium"),
	("Tb", "Terbium"),
	("Dy", "Dysprosium"),
	("Ho", "Holmium"),
	("Er", "Erbium"),
	("Tm", "Thulium"),
	("Yb", "Ytterbium"),
	("Lu", "Lutetium"),
	("Hf", "Hafnium"),
	("Ta", "Tantalum"),
	("W", "Tungsten"),
	("Re", "Rhenium"),
	("Os", "Osmium"),
	("Ir", "Iridium"),
	("Pt", "Platinum"),
	("Au", "Gold"),
	("Hg", "Mercury"),
	("Tl", "Thallium"),
	("Pb", "Lead"),
	("Bi", "Bismuth"),
	("Po", "Polonium"),
	("At", "Astatine"),
	("Rn", "Radon"),
	("Fr", "Francium"),
	("Ra", "Radium"),
	("Ac", "Actinium"),
	("Th", "Thorium"),
	("Pa", "Protactinium"),
	("U", "Uranium"),
	("Np", "Neptunium"),
	("Pu", "Plutonium"),
	("Am", "Americium"),
	("Cm", "Curium"),
	("Bk", "Berkelium"),
	("Cf", "Californium"),
	("Es", "Einsteinium"),
	("Fm", "Fermium"),
	("Md", "Mendelevium"),
	("No", "Nobelium"),
	("Lr", "Lawrencium"),
	("Rf", "Rutherfordium"),
	("Db", "Dubnium"),
	("Sg", "Seaborgium"),
	("Bh", "Bohrium"),
	("Hs", "Hassium"),
	("Mt", "Meitnerium"),
	("Ds", "Darmstadtium"),
	("Rg", "Roentgenium"),
	("Cn", "Copernicium"),
	("Nh", "Nihonium"),
	("Fl", "Flerovium"),
	("Mc", "Moscovium"),
	("Lv", "Livermorium"),
	("Ts", "Tennessine"),
	("Og", "Oganesson"),
	# Isotopes, but hey, they make the words look better
	("D", "Deuterium"),
	("T", "Tritium"),
	# Non-elements and eastereggs
	("E", "Euphorium"),
	("Xyzzy", "Plugh"),
	("Plugh", "Xyzzy"),
	("hunter2", "*******"),
]
ELEMDICT = {symbol.lower(): name for (symbol, name) in ELEMENTS}
ELEMLENGTHS = set(len(symbol) for (symbol, _) in ELEMENTS)

class Node:
	def __init__(self, stump):
		self.stump = stump
		self.edges = []

class Edge:
	LETTER = 0
	ELEMENT = 1

	def __init__(self, start, end, weight, edgetype, text):
		self.start = start
		self.end = end
		self.weight = weight
		self.edgetype = edgetype
		self.text = text

def elem_prefixes(text):
	elems = []
	for i in ELEMLENGTHS:
		if len(text) < i: continue

		start, rest = text[:i], text[i:]
		elem = ELEMDICT.get(start.lower(), None)
		if elem:
			elems.append((elem, rest))

	return elems

def create_graph(text):
	graph = {}
	stumps = [text[i:] for i in range(len(text))]

	# goal node
	graph[""] = Node("")

	# creating all the nodes
	for stump in stumps:
		graph[stump] = Node(stump)

	# creating single-letter links
	weight = len(text)
	for start in stumps:
		char, end = start[:1], start[1:]
		nstart = graph.get(start)
		nend = graph.get(end)
		edge = Edge(nstart, nend, weight, Edge.LETTER, char)
		nstart.edges.append(edge)

	# creating element links
	for stump in stumps:
		elems = elem_prefixes(stump)
		for (elem, rest) in elems:
			nstart = graph.get(stump)
			nend = graph.get(rest)
			edge = Edge(nstart, nend, 1, Edge.ELEMENT, elem)
			nstart.edges.append(edge)

	return graph

def smallest(graph, nodes):
	smallest = None
	for node in nodes:
		if not smallest or node.length < smallest.length:
			smallest = node
	return smallest

def dijkstra(graph, start, end):
	unvisited = set()
	visited = set()

	nstart = graph.get(start)
	nstart.step = None
	nstart.length = 0
	for edge in nstart.edges:
		node = edge.end
		unvisited.add(node)
		node.step = edge
		node.length = edge.weight
	visited.add(nstart)

	while unvisited:
		small = smallest(graph, unvisited)
		unvisited.remove(small)
		visited.add(small)

		if small.stump == "":
			break

		for edge in small.edges:
			node = edge.end
			if node in visited: continue
			length = small.length + edge.weight
			if node in unvisited:
				if length < node.length:
					node.step = edge
					node.length = length
			else:
				unvisited.add(node)
				node.step = edge
				node.length = length

	path = []
	node = graph.get(end)
	while node.step:
		path.append(node.step)
		node = node.step.start

	return reversed(path)

def format_path(path):
	parts = []
	part = ""

	for edge in path:
		if edge.edgetype == Edge.LETTER:
			part += edge.text
		else:
			if part:
				parts.append(part)
				part = ""
			parts.append(edge.text)

	if part:
		parts.append(part)

	return "-".join(parts)

def shortest_path(text):
	graph = create_graph(text)
	path = dijkstra(graph, text, "")
	return path

class Tom(yaboli.Module):
	DESCRIPTION = (
		"'tom' attempts to spell a word using the symbols of the periodic table."
		" For example, 'Hi' becomes 'Hydrogen Iodine'.\n"
		"Because of this, only the letters a-z and A-Z may be used in a word.\n"
		"'tom' uses en.wikipedia.org/wiki/List_of_chemical_elements for the element names.\n"
	)
	COMMANDS = "!tom <word> - attempts to spell the word using chemical elements\n"
	AUTHOR = "Created by @Garmy using github.com/Garmelon/yaboli\n"
	CREDITS = "Inspired by Tomsci. Algorithm based on a suggestion by Xyzzy.\n"

	SHORT_DESCRIPTION = "spell a word using chemical elements, if possible"
	SHORT_HELP =   "/me spells a word using chemical elements, if possible"

	LONG_DESCRIPTION = DESCRIPTION + COMMANDS          + CREDITS
	LONG_HELP        = DESCRIPTION + COMMANDS + AUTHOR + CREDITS

	ALLOWED_CHARS = r"a-zA-Z*\w"
	ELEM_RE = "([" + ALLOWED_CHARS + "]*)([^" + ALLOWED_CHARS + "]*)"

	async def on_command_general(self, room, message, command, argstr):
		await self.command_tom(room, message, command, argstr)

	@yaboli.command("tom")
	async def command_tom(self, room, message, argstr):
		args = []
		while argstr:
			match = re.match(self.ELEM_RE, argstr)
			if not match: break

			args.append((match.group(1), match.group(2)))
			argstr = argstr[match.end():]

		spellings = []
		for fst, snd in args:
			if fst:
				spelling = format_path(shortest_path(fst)) + snd
			else:
				spelling = snd
			spellings.append(spelling)

		text = "".join(spellings)
		await room.send(text, message.mid)

def main(configfile):
	logging.basicConfig(level=logging.INFO)

	config = configparser.ConfigParser(allow_no_value=True)
	config.read(configfile)

	nick = config.get("general", "nick")
	cookiefile = config.get("general", "cookiefile", fallback=None)
	module = Tom()

	bot = yaboli.ModuleBot(module, nick, cookiefile=cookiefile)

	for room, password in config.items("rooms"):
		if not password:
			password = None
		bot.join_room(room, password=password)

	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main("tom.conf")
