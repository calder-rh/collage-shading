from pymel.core import *
from internals import network

def run():
    confirmDialog(t='Success', m='Last updated Saturday April 27', b=['OK'], ma='left')

def error(msg):
    confirmDialog(t='Error', m=msg, b=['OK'], ma='left')