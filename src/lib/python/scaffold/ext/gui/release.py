#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import json
import pprint
from argparse import Namespace

from rlp.Qt import QStr, QVMap, QV
from rlp import QtGui
import rlp.gui as RlpGui
import rlp.util as RlpUtil

import RlpGuiPANEmodule

from scaffold.ext import sset_release

from . import edbc

VIEW = RlpGuiPANEmodule.VIEW

_PANELS = []
_DIALOGS = []

class NewSoftwareSetDialog(RlpGui.GUI_ItemBase):

    def __init__(self, fp, project, sset_name, sset_config, config_path):
        RlpGui.GUI_ItemBase.__init__(self, fp.body())

        fp.setText('Release Software Set')
        fp.setTextBold(True)
        self._fpane = fp
        self.setZValue(fp.z())

        self.project = project
        self.sset_name = sset_name
        self.sset_config = sset_config
        self.sc_config_path = config_path
        

        self.sset_name_label = RlpGui.GUI_Label(self, 'Software Set: {}'.format(sset_name))
        self.sset_version_label = RlpGui.GUI_Label(self, 'Version:')
        self.sset_version_text = RlpGui.GUI_TextEdit(self, 150, 60)
        self.sset_version_text.setText(sset_config['sftset_version'])

        self.sset_ver_layout = RlpGui.GUI_HLayout(self)
        self.sset_ver_layout.addItem(self.sset_version_label, 0)
        self.sset_ver_layout.addItem(self.sset_version_text, 0)

        self.project_builds = []


        proj_result = edbc.calls('edbc.find', 'Project', [['name', 'is', self.project]], [])
        print(proj_result)
        if proj_result:
            self.project_builds = edbc.calls('edbc.find', 'BuildVersion',
                [
                    ['project', 'is', proj_result[0]]
                ],
                ['version']
            )


        self.link_build = RlpGui.GUI_RadioButton(self, 'Link to Build:', 20, 0)
        self.link_build.setToggled(True)
        self.link_build.buttonPressed.connect(self.toggle_link)
        self.link_layout = RlpGui.GUI_HLayout(self)

        self.builds_btn = RlpGui.GUI_IconButton('', self, 20, 4)
        self.builds_btn.setOutlined(True)
        self.builds_btn.setText('Build:')
        self.builds_btn.setSvgIconPath(':feather/lightgrey/chevron-down.svg', 20)
        self.builds_btn.menu().menuItemSelected.connect(self.on_build_selected)

        si = self.builds_btn.svgIcon()
        si.setFgColour(QtGui.QColor(140, 140, 140)) # QtCore.Qt.red)
        si.setBgColour(QtGui.QColor(140, 140, 140)) # QtCore.Qt.red)
        si.setPos(si.x(), 4)


        for proj_build in self.project_builds:
            self.builds_btn.menu().addItem(
                proj_build['version'],
                {},
                False
            )
        
        self.link_layout.addItem(self.link_build, 0)
        self.link_layout.addItem(self.builds_btn, 0)

        self.release_button = RlpGui.GUI_IconButton('', self, 20, 4)
        self.release_button.setText('Release Software Set')
        self.release_button.setOutlined(True)
        self.release_button.buttonPressed.connect(self.on_release)

        self.cancel_button = RlpGui.GUI_IconButton('', self, 20, 4)
        self.cancel_button.setText('Cancel')
        self.cancel_button.setOutlined(True)
        self.cancel_button.buttonPressed.connect(self.close)

        self.button_layout = RlpGui.GUI_HLayout(self)
        self.button_layout.addSpacer(40)
        self.button_layout.addItem(self.release_button, 0)
        self.button_layout.addSpacer(20)
        self.button_layout.addItem(self.cancel_button, 0)

        self.layout = RlpGui.GUI_VLayout(self)
        self.layout.addSpacer(20)
        self.layout.addItem(self.sset_name_label, 0)
        self.layout.addItem(self.sset_ver_layout, 0)
        self.layout.addItem(self.link_layout, 0)
        self.layout.addSpacer(30)
        self.layout.addItem(self.button_layout, 0)


        self.onParentSizeChangedItem(fp.width(), fp.height())



    def onParentSizeChangedItem(self, width, height):

        self.setItemWidth(width)
        self.setItemHeight(height)


    def close(self, md=None):
        self._fpane.requestClose()

    def on_build_selected(self, md):
        self.builds_btn.setText(md['text'])

    def toggle_link(self, md=None):
        self.link_build.setToggled(not self.link_build.isToggled())

    def on_release(self, md=None):
        
        if self.link_build.isToggled() and ':' in build_version:
            print('Version not specified')
            return

        rel_sset_args = Namespace(
            project=self.project,
            sset=self.sset_name,
            config_path=self.sc_config_path,
            release_num=None
        )

        release_num = sset_release.release_sset(rel_sset_args)
        build_version = self.builds_btn.text()
        if ':' in build_version:
            print('Version not specified')
            return

        if self.link_build.isToggled():
            link_args = Namespace(
                project=self.project,
                sset=self.sset_name,
                sset_version=self.sset_config['sftset_version'],
                release_num=release_num,
                build_version=build_version,
                sset_project=None
            )

            sset_release.link_sset(link_args)


class NewBuildDialog(RlpGui.GUI_ItemBase):

    def __init__(self, fp, project, config_path):
        RlpGui.GUI_ItemBase.__init__(self, fp.body())

        self.project = project
        self.sc_config_path = config_path

        fp.setText('New Build')
        fp.setTextBold(True)
        self._fpane = fp
        self.setZValue(fp.z())

        self.project_label = RlpGui.GUI_Label(self, 'Project: {}'.format(project))
        self.config_path_label = RlpGui.GUI_Label(self, 'Config: {}'.format(self.sc_config_path))
        
        self.build_version_label = RlpGui.GUI_Label(self, 'Build Version:')
        self.build_version_text = RlpGui.GUI_TextEdit(self, 150, 60)

        self.bv_layout = RlpGui.GUI_HLayout(self)
        self.bv_layout.addItem(self.build_version_label, 0)
        self.bv_layout.addItem(self.build_version_text, 0)

        self.btn_layout = RlpGui.GUI_HLayout(self)
        self.release_button = RlpGui.GUI_IconButton('', self, 20, 4)
        self.release_button.setText('Release New Build')
        self.release_button.setOutlined(True)
        self.release_button.buttonPressed.connect(self.release_build)

        self.cancel_button = RlpGui.GUI_IconButton('', self, 20, 4)
        self.cancel_button.setText('Cancel')
        self.cancel_button.setOutlined(True)
        self.cancel_button.buttonPressed.connect(self.close)

        self.btn_layout.addSpacer(40)
        self.btn_layout.addItem(self.release_button, 0)
        self.btn_layout.addSpacer(20)
        self.btn_layout.addItem(self.cancel_button, 0)

        self.layout = RlpGui.GUI_VLayout(self)
        self.layout.addSpacer(20)
        self.layout.addItem(self.config_path_label, 0)
        self.layout.addItem(self.project_label, 0)
        self.layout.addItem(self.bv_layout, 0)
        self.layout.addSpacer(20)
        self.layout.addItem(self.btn_layout, 0)


        self.onParentSizeChangedItem(fp.width(), fp.height())


    def onParentSizeChangedItem(self, width, height):

        self.setItemWidth(width)
        self.setItemHeight(height)


    def close(self, md=None):
        self._fpane.requestClose()

    
    def release_build(self, md=None):
        print('RELEASE')

        build_version = self.build_version_text.text()
        args = Namespace(
            site='rlp_test',
            project=self.project,
            version=build_version,
            config_path=self.sc_config_path
        )

        sset_release.release_build(args)

        self.close()



class BuildPanel(RlpGui.GUI_ItemBase):

    def __init__(self, parent):
        RlpGui.GUI_ItemBase.__init__(self, parent)

        self.project = None
        self.sc_config = None
        self.sc_config_path = None
        self.ssets = {}

        self.layout = RlpGui.GUI_VLayout(self)

        self.toolbar_layout = RlpGui.GUI_HLayout(self)
        self.btn_release_build = RlpGui.GUI_IconButton('', self, 20, 4)
        self.btn_release_build.setText('Release New Build')
        self.btn_release_build.setOutlined(True)
        self.btn_release_build.buttonPressed.connect(self.on_release_new_build)

        self.toolbar_layout.addSpacer(10)
        self.toolbar_layout.addItem(self.btn_release_build, 0)

        self.project_label = RlpGui.GUI_Label(self, 'Project: ')
        self.config_path_label = RlpGui.GUI_Label(self, 'Config:')

        self.layout.addSpacer(10)
        self.layout.addItem(self.toolbar_layout, 0)
        self.layout.addSpacer(10)
        self.layout.addItem(self.project_label, 0)
        self.layout.addItem(self.config_path_label, 0)
        self.layout.addSpacer(10)

        self._init_config()


    def _init_config(self):

        ag = RlpUtil.APPGLOBALS.globals()
        self.sc_config_path = ag['startup.args'][2]

        self.config_path_label.setText('Config: {}'.format(self.sc_config_path))

        with open(self.sc_config_path) as fh:
            self.sc_config = json.load(fh)

            for sset_name, sset_config in self.sc_config.items():

                if sset_name == '__bootstrap__':
                    if 'project' in sset_config:
                        self.project = sset_config['project']
                        self.project_label.setText('Project: {}'.format(self.project))
                    continue

                print(sset_name)
                pprint.pprint(sset_config)

                
                lbl_sset_name = RlpGui.GUI_Label(self, sset_name)
                lbl_sset_ver = RlpGui.GUI_Label(self, sset_config['sftset_version'])
                btn_rel = RlpGui.GUI_IconButton('', self, 20, 4)
                btn_rel.setText('Release')
                btn_rel.setOutlined(True)
                btn_rel.setMetadata('sset_name'), QV(sset_name)
                btn_rel.setMetadata('sset_config'), QV(sset_config)
                btn_rel.buttonPressed.connect(self.on_sset_release_requested)

                sset_layout = RlpGui.GUI_HLayout(self)
                sset_layout.addItem(lbl_sset_name, 0)
                sset_layout.addSpacer(5)
                sset_layout.addItem(lbl_sset_ver, 0)
                sset_layout.addSpacer(10)
                sset_layout.addItem(btn_rel, 0)

                self.ssets[sset_name] = {
                    'layout': sset_layout,
                    'label': lbl_sset_name,
                    'ver': lbl_sset_ver,
                    'btn_rel': btn_rel
                }
                self.layout.addItem(sset_layout, 0)


    def on_release_new_build(self, md):
        
        fp = VIEW.createFloatingPane(400, 300, False)
        diag = NewBuildDialog(fp, self.project, self.sc_config_path)
        _DIALOGS.append(diag)

    def on_sset_release_requested(self, md):

        fp = VIEW.createFloatingPane(400, 300, False)
        diag = NewSoftwareSetDialog(
            fp,
            self.project,
            md['sset_name'],
            md['sset_config'],
            self.sc_config_path
        )
        _DIALOGS.append(diag)



    def onParentSizeChangedItem(self, width, height):

        self.setItemWidth(width)
        self.setItemHeight(height)




def create(parent):
    build_panel = BuildPanel(parent)

    global _PANELS
    _PANELS.append(build_panel)
    return build_panel