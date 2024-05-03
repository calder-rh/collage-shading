from pymel.core import *
from internals import network

def run():
    confirmDialog(t='Success', m='Last updated Friday May 3', b=['OK'], ma='left')

def error(msg):
    confirmDialog(t='Error', m=msg, b=['OK'], ma='left')