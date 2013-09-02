__author__ = 'Nathan'

import uuid
import base64
import logging

log = logging.getLogger(__name__)

def generateGuid(length=None):
	"""
	URL Safe and Unique GUID Generator

	:return: GUID
	:rtype: str
	"""
	r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
	r_uuid = r_uuid.replace('=', '')
	if length:
		r_uuid = r_uuid[:length]
	return r_uuid


def removeDuplicates(seq):
	"""
	| Fastest order preserving way to make a list unique
	| http://www.peterbe.com/plog/uniqifiers-benchmark
	| Specific method by: ``Dave Kirby``

	:param seq: Input sequence
	:type seq: list
	:return: Unique sequence
	:rtype: list
	"""
	seen = set()
	return [x for x in seq if x not in seen and not seen.add(x)]

def clamp(minimum, maximum, value):
	"""
	Clamp value between min and max

	:param minimum: min value
	:type minimum: float
	:param maximum: max value
	:type maximum: float
	:param value: input value
	:type value: float
	:return: value, where min<=value<=max
	:rtype: float
	"""
	#return sorted([minimum, maximum, value])[1]  #Alternate way
	return max(minimum, min(value, maximum))

def closest(values, value):
	"""
	Get the closest value from a list of values.

	:param values: values to check
	:type values: list
	:param value: target value
	:type value: float or int
	:return: closest value
	:rtype: float or int
	"""
	return min(values, key=lambda x: abs(x-value))