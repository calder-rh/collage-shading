from pymel.core import *
from internals import network

def run():
    confirmDialog(t='Success', m='Last updated Friday April 12 at 11am', b=['OK'], ma='left')

def error(msg):
    confirmDialog(t='Error', m=msg, b=['OK'], ma='left')