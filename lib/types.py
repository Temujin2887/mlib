__author__ = 'Nathan'



def Enum(*sequential, **named):
	"""
	Enum Class Factory

	Works using an enumerated list:
	>>> Types = Enum('test1', 'test2', 'test3')

	Or using key/value pairs:
	>>> Types = Enum(test1=0, test2=1, test3=2)

	And conversion for keys<==>values:

	>>> print Types.key(0)
	test1

	>>> print Types.value('test1')
	0

	The Enum objects provide dot access for the values:

	>>> print Types.test1
	0

	:return: Created enum
	:rtype: :py:class:`.Enum`
	"""
	base_enums = dict(zip(sequential, range(len(sequential))), **named)
	reverse = dict((value, key) for key, value in base_enums.iteritems())
	enums = base_enums.copy()
	enums['key'] = reverse.get
	enums['value'] = enums.get
	metaclass = type('Enum', (type,), {'__repr__':lambda cls: repr(base_enums)})
	return metaclass('Enum', (object,), enums)

class PropertyDict(dict):
	"""
	Subclass of dict that allows the user to access keys as properties
	"""
	def __getattr__(self, key):
		try:
			return dict.__getattribute__(self, key)
		except:
			return self.__getitem__(key)

	def __setattr__(self, key, value):
		dict.__setitem__(self, key, value)

	def _setattr(self, key, value):
		object.__setattr__(self, key, value)