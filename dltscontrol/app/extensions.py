""" 
Imports all modules into the final dlts control application. Be aware that import order matters and could eventually lead to compilation problems. 
"""

import dltscontrol.app.core
import dltscontrol.app.scanning
import dltscontrol.app.scandataviewing

import dltscontrol.app.serial

import dltscontrol.app.configparseruserconfig
import dltscontrol.app.serialdlts

import dltscontrol.app.scandatabinarysaving
import dltscontrol.app.arrayimagesaving
import dltscontrol.app.arraytextsaving
import dltscontrol.app.dictjsonsaving

import dltscontrol.app.controller
import dltscontrol.app.scanner
import dltscontrol.app.scandataviewer

import dltscontrol.app.reflectionscanning
import dltscontrol.app.latchupscanning
import dltscontrol.app.comboscanning
import dltscontrol.app.parallelscanning
import dltscontrol.app.currentscanning
import dltscontrol.app.multiintscan

#import dltscontrol.app.examples
