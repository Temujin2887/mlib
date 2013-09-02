__author__ = 'Nathan'



def Enum(*sequential, **named):
	"""
	Enum Class Factory
	Works using an enumerated list::
		Types = Enum('test1', 'test2', 'test3')
	Or using key/value pairs::
		Types = Enum(test1=0, test2=1, test3=2)

	And conversion for keys<==>values::
		print Types.key(0)
		print Types.value('test1')

	The Enum objects provide dot access for the values::
		print Types.test1

	:return: Created enum
	:rtype: :py:class:`.Enum`
	"""
	enums = dict(zip(sequential, range(len(sequential))), **named)
	reverse = dict((value, key) for key, value in enums.iteritems())
	enums['key'] = reverse.get
	enums['value'] = enums.get
	return type('Enum', (), enums)

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