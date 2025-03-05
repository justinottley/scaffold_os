#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import sys

from rlp.Qt import QVMap, QStr

import RlpGuiPANEmodule
import RlpProdLAUNCHmodule

from rlp.core.net.websocket.standalone import StandaloneWsClient

from scaffold.ext import sset_release

VIEW = RlpGuiPANEmodule.VIEW
CNTRL = RlpProdLAUNCHmodule.CNTRL


# The sset_release module requires the standalone client
# so we are using that in the UI as well
#
edbc = StandaloneWsClient.init('wss://127.0.0.1:8003')
edbc.connect()

sset_release.edbc = edbc

release_tool = {
    'name': 'SSet Release',
    'item_type': 'tool',
    'pyitem': 'scaffold.ext.gui.release'
}


builds_tool = {
    'name': 'Builds',
    'item_type': 'tool',
    'pyitem': 'scaffold.ext.gui.builds'
}


VIEW.registerToolGUI(builds_tool)
VIEW.registerToolGUI(release_tool)

CNTRL.openTool('SSet Release')
CNTRL.openTool('Builds')
CNTRL.openTool('SSet Release')


