#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import json
from argparse import Namespace

from rlp.Qt import QStr, QVMap, QV
from rlp import QtGui
import rlp.gui as RlpGui
import rlp.util as RlpUtil

import RlpGuiPANEmodule
VIEW = RlpGuiPANEmodule.VIEW

_PANELS = []
_DIALOGS = []

from scaffold.ext import sset_release

from . import edbc


class LinkNewSSetReleaseDialog(RlpGui.GUI_ItemBase):

    def __init__(self, fp, project_entity, build_sset, build_version):
        RlpGui.GUI_ItemBase.__init__(self, fp.body())

        self._fpane = fp

        fp.setText('Link New Software Set')
        fp.setTextBold(True)

        print(project_entity)
        self.project_entity = project_entity
        self.build_sset = build_sset
        self.build_version = build_version
        print(build_version)

        self.sset_label = RlpGui.GUI_Label(self,
            '{}.{} - {}'.format(
                self.project_entity['name'],
                self.build_version['version'],
                self.build_sset['sset_name'])
        )

        self.sset_rel_chooser = RlpGui.GUI_IconButton('', self, 20, 4)
        self.sset_rel_chooser.setText('Release:')
        self.sset_rel_chooser.setOutlined(True)
        self.sset_rel_chooser.setSvgIconPath(':feather/lightgrey/chevron-down.svg', 20)
        self.sset_rel_chooser.menu().menuItemSelected.connect(self.on_sset_rel_selected)
        # self.sset_rel_chooser.setMenuYOffset(-50) # WHY??
        si = self.sset_rel_chooser.svgIcon()
        si.setFgColour(QtGui.QColor(140, 140, 140)) # QtCore.Qt.red)
        si.setBgColour(QtGui.QColor(140, 140, 140)) # QtCore.Qt.red)
        si.setPos(si.x(), 4)

        self._init_project_sset_releases()

        self.sset_layout = RlpGui.GUI_HLayout(self)
        self.sset_layout.addSpacer(22)
        self.sset_layout.addItem(self.sset_rel_chooser, 0)

        self.update_button = RlpGui.GUI_IconButton('', self, 20, 4)
        self.update_button.setText('Update')
        self.update_button.setOutlined(True)
        self.update_button.buttonPressed.connect(self.update_requested)

        self.cancel_button = RlpGui.GUI_IconButton('', self, 20, 4)
        self.cancel_button.setText('Cancel')
        self.cancel_button.setOutlined(True)
        self.cancel_button.buttonPressed.connect(self.close)


        self.btn_layout = RlpGui.GUI_HLayout(self)
        self.btn_layout.addSpacer(80)
        self.btn_layout.addItem(self.update_button, 0)
        self.btn_layout.addSpacer(40)
        self.btn_layout.addItem(self.cancel_button, 0)


        self.layout = RlpGui.GUI_VLayout(self)
        self.layout.addSpacer(20)
        self.layout.addItem(self.sset_label, 20)
        self.layout.addSpacer(10)
        self.layout.addItem(self.sset_layout, 0)
        self.layout.addSpacer(30)
        self.layout.addItem(self.btn_layout, 0)

        self.onParentSizeChangedItem(fp.width(), fp.height())


    def _init_project_sset_releases(self):

        sset_rel_result = edbc.calls('edbc.find', 'SoftwareSetRelease',
            [
                ['project', 'is', self.project_entity]
            ],
            ['name', 'project', 'sset_name', 'sset_version', 'sset_release_num']
        )

        for sset_rel in sset_rel_result:

            self.sset_rel_chooser.menu().addItem(
                sset_rel['name'],
                sset_rel,
                False
            )

            print(sset_rel)


    def on_sset_rel_selected(self, md):
        print(md)
        self._sel = md['data']
        self.sset_rel_chooser.setText(md['data']['name'])


    def update_requested(self, md=None):

        args = Namespace(
            project=self.project_entity['name'],
            build_version=self.build_version['version'],
            sset=self._sel['sset_name'],
            sset_project=self._sel['project']['name'],
            sset_version=self._sel['sset_version'],
            release_num=self._sel['sset_release_num']
        )

        sset_release.link_sset(args)

        self.close()


    def close(self, md=None):
        self._fpane.requestClose()


    def onParentSizeChangedItem(self, width, height):

        self.setItemWidth(width)
        self.setItemHeight(height)



class BuildsPanel(RlpGui.GUI_ItemBase):

    def __init__(self, parent):
        RlpGui.GUI_ItemBase.__init__(self, parent)

        self.project = None
        self.ssets = {}

        self.project_label = RlpGui.GUI_Label(self, '')

        self.build_chooser = RlpGui.GUI_IconButton('', self, 20, 4)
        self.build_chooser.setText('Build:')
        self.build_chooser.setOutlined(True)
        self.build_chooser.setSvgIconPath(':feather/lightgrey/chevron-down.svg'), 20
        self.build_chooser.menu().menuItemSelected.connect(self.on_project_selected)

        si = self.build_chooser.svgIcon()
        si.setFgColour(QtGui.QColor(140, 140, 140)) # QtCore.Qt.red)
        si.setBgColour(QtGui.QColor(140, 140, 140)) # QtCore.Qt.red)
        si.setPos(si.x(), 4)
    
        self.proj_layout = RlpGui.GUI_HLayout(self)
        self.proj_layout.addSpacer(20)
        self.proj_layout.addItem(self.project_label, 0)
        self.proj_layout.addItem(self.build_chooser, 0)

        self.layout = RlpGui.GUI_VLayout(self)
        self.layout.addSpacer(10)
        self.layout.addItem(self.proj_layout, 0)
        self.layout.addSpacer(20)

        self._init_project_builds()

        self.onParentSizeChangedItem(parent.width(), parent.height())


    def _init_project_builds(self):

        ag = RlpUtil.APPGLOBALS.globals()
        self.sc_config_path = ag['startup.args'][2]

        print(self.sc_config_path)

        with open(self.sc_config_path) as fh:
            self.sc_config = json.load(fh)

            for sset_name, sset_config in self.sc_config.items():

                if sset_name == '__bootstrap__':
                    if 'project' in sset_config:
                        self.project = sset_config['project']
                        self.project_label.setText('Project: {}'.format(self.project))
                    break

        if not self.project:
            return

        project_result = edbc.calls('edbc.find', 'Project', [['name', 'is', self.project]], ['name'])
        if not project_result:
            print('ERROR: invalid project: {}'.format(self.project))
            return

        self.project_entity = project_result[0]

        builds = edbc.calls('edbc.find', 'BuildVersion',
            [['project', 'is', self.project_entity]], ['version'])

        for build_entry in builds:
            self.build_chooser.menu().addItem(
                build_entry['version'],
                build_entry,
                False
            )


    def on_project_selected(self, md):
        print(md)
        build_version = md['text']
        self.build_chooser.setText(build_version)


        build_ssets = edbc.calls('edbc.find', 'BuildSoftwareSet',
            [
                ['build_version', 'is', md['data']]
            ],
            ['sset_name', 'sset_release']
        )

        for build_sset in build_ssets:
            
            print(build_sset)
            print('')
            sset_name = build_sset['sset_name']
            sset_release_name = build_sset['sset_release']['name']

            # split on dot to get info..
            sset_rel_parts = sset_release_name.split('.')
            sset_rel_num = sset_rel_parts[-1]
            sset_rel_ver = '.'.join(sset_rel_parts[2:-1])

            sset_layout = RlpGui.GUI_HLayout(self)

            sset_label = RlpGui.GUI_Label(self, sset_name)
            sset_label.setItemWidth(80)
            sset_version = RlpGui.GUI_Label(self, '{}'.format(sset_rel_ver))
            sset_version.setItemWidth(120)
            sset_rel_num = RlpGui.GUI_Label(self, 'Rel Num: {}'.format(sset_rel_num))
            sset_rel_num.setItemWidth(100)

            change_btn = RlpGui.GUI_IconButton('', self, 20, 4)
            change_btn.setText('Change')
            change_btn.setOutlined(True)
            change_btn.setMetadata(
                'build_sset',
                QV(build_sset)
            )
            change_btn.setMetadata(
                'build_version',
                QV(md['data'])
            )
            change_btn.buttonPressed.connect(self.on_change_sset_requested)

            sset_layout.addSpacer(10)
            sset_layout.addItem(sset_label, 0)
            sset_layout.addItem(sset_version, 0)
            sset_layout.addItem(sset_rel_num, 0)
            sset_layout.addSpacer(10)
            sset_layout.addItem(change_btn, 0)

            self.ssets[sset_name] = {
                'layout': sset_layout,
                'label': sset_label,
                'ver': sset_version,
                'relnum': sset_rel_num,
                'change_btn': change_btn
            }

            self.layout.addItem(sset_layout, 0)


    def on_change_sset_requested(self, md=None):
        print(md)

        fpane = VIEW.createFloatingPane(380, 280, False)
        diag = LinkNewSSetReleaseDialog(
            fpane,
            self.project_entity,
            md['build_sset'],
            md['build_version']
        )

        _DIALOGS.append(diag)



    def onParentSizeChangedItem(self, width, height):

        self.setItemWidth(width)
        self.setItemHeight(height)



def create(parent):
    build_panel = BuildsPanel(parent)

    global _PANELS
    _PANELS.append(build_panel)
    return build_panel