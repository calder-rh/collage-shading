from pymel.core import *
import sys, webbrowser, subprocess

def dialog_with_support(title, msg, buttons, **kwargs):
    dialog_output = confirmDialog(t=title, m=msg, b=['What?'] + buttons, ma='left', **kwargs)
    if dialog_output == 'What?':
        webbrowser.open('slack://channel?id=C05BFV55GLT&team=T05B9C5MHKQ')
        dialog_output = confirmDialog(t='Would you like to copy the error message to your clipboard?', m=title + '\n' + msg, b=['Yes', 'No'], cb='No', db='Yes', icon='question', ma='left')
        if dialog_output == 'Yes':
            if sys.platform == 'darwin':
                copy_keyword = 'pbcopy'
            elif sys.platform == 'win32':
                copy_keyword = 'clip'
            subprocess.run(copy_keyword, universal_newlines=True, input=title + '\n' + msg)
        exit()
    else:
        return dialog_output
