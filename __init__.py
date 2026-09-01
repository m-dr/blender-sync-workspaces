# Blender add-on - Synchronize 3D views between workspaces
# Copyright (C) 2024 Michael Soluyanov (multlabs.com)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


import copy
import bpy
from bpy.app.handlers import persistent

from . import tools

bl_info = {
    "name": "Synchronize Workspaces",
    "author": "Michael Soluyanov (multlabs.com)",
    "version": (1, 15),
    "blender": (4, 2, 0),
    "location": "View3D -> Top Bar",
    "description": "Synchronize 3D views between workspaces",
    "warning": "",
    "doc_url": "https://blenderartists.org/t/synchronize-workspaces-blender-add-on/1356695",
    "category": "Interface",
}


class sinchmanager_class:
    last_area = ""
    last_workspace = ""


def check_screen(sc):
    for window in bpy.context.window_manager.windows:
        if window.screen == sc:
            return True
    return False


def get_biggest_area(workspace, type, checkscreen=False, ignore_temp=True):
    max_size = 0
    nextArea = None
    for screen in workspace.screens:
        if ignore_temp and screen.name.startswith("temp"):
            continue
        if(checkscreen):
            if not check_screen(screen):
                continue
        for area in screen.areas:
            if area.type == type:
                size = area.width * area.height
                if size > max_size:
                    nextArea = area
                    max_size = size
    # Fallback to include temp screens only if no normal screen area was found
    if nextArea is None and ignore_temp:
        return get_biggest_area(workspace, type, checkscreen=checkscreen, ignore_temp=False)
    return nextArea


def _remember_sync_source(workspace, area=None):
    """Store the last sync-enabled workspace/view used as copy source."""
    sinchmanager.last_workspace = workspace.name
    if area is None:
        area = get_biggest_area(workspace, "VIEW_3D", True)
    sinchmanager.last_area = area


def update_workspace(args):
    """Copy 3D view from the last sync-enabled workspace into the current one.

    Workspaces with synch_active off are skipped: visiting them does not change
    the remembered source, so the next sync-enabled workspace still receives
    the view from the previous sync-enabled workspace.
    """
    if not bpy.context.scene.synch_settings.active:
        return
    # Sync-disabled workspace: leave last_* pointing at the last enabled source
    if not bpy.context.workspace.synch_active:
        return

    next1 = bpy.context.workspace
    if sinchmanager.last_workspace == next1.name:
        return
    if sinchmanager.last_workspace not in bpy.data.workspaces:
        _remember_sync_source(next1)
        return

    prev = bpy.data.workspaces[sinchmanager.last_workspace]
    nextArea = get_biggest_area(next1, "VIEW_3D", True)

    # First prefer sinchmanager.last_area if it belongs to prev
    prevArea = None
    if sinchmanager.last_area:
        for sc in prev.screens:
            if not sc.name.startswith("temp") and sinchmanager.last_area in list(sc.areas):
                prevArea = sinchmanager.last_area
                break

    # Resolve source from the remembered sync-enabled workspace (ignoring inactive temp screens)
    if prevArea is None:
        prevArea = get_biggest_area(prev, "VIEW_3D", False, ignore_temp=True)
    if prevArea is None:
        prevArea = sinchmanager.last_area

    if nextArea is None:
        return
    if prevArea is None:
        _remember_sync_source(next1, nextArea)
        return

    for ns3d in nextArea.spaces:
        if ns3d.type == "VIEW_3D":
            break
    for ps3d in prevArea.spaces:
        if ps3d.type == "VIEW_3D":
            break

    nr3d = ns3d.region_3d
    pr3d = ps3d.region_3d

    if (ps3d.local_view is not None):
        objects = [ob for ob in bpy.context.view_layer.objects
                   if ob.visible_get(viewport=ps3d)]

        selected = bpy.context.selected_objects[:]
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.update()
        if (ns3d.local_view is None):

            context_override = bpy.context.copy()
            context_override["area"]  = nextArea
            with bpy.context.temp_override(**context_override):
                bpy.ops.view3d.localview(frame_selected=False)
        else:
            objectsn = [ob for ob in bpy.context.view_layer.objects
                        if ob.visible_get(viewport=ns3d)]
            for obj in objects:
                if obj not in objectsn:
                    obj.local_view_set(ns3d, True)
                obj.select_set(obj in selected)
            for obj in objectsn:
                if obj not in objects:
                    obj.local_view_set(ns3d, False)
            bpy.context.view_layer.update()

    elif (ns3d.local_view is not None) and (ps3d.local_view is None):
        context_override = bpy.context.copy()
        context_override["area"]  = nextArea
        with bpy.context.temp_override(**context_override):
            bpy.ops.view3d.localview(frame_selected=False)

    # region 3d settings:
    nr3d.view_distance = pr3d.view_distance
    nr3d.view_matrix = copy.copy(pr3d.view_matrix)

    nr3d.is_orthographic_side_view = pr3d.is_orthographic_side_view
    nr3d.is_perspective = pr3d.is_perspective
    nr3d.view_perspective = pr3d.view_perspective
    nr3d.view_rotation = pr3d.view_rotation
    nr3d.is_orthographic_side_view = pr3d.is_orthographic_side_view

    nr3d.view_camera_offset = pr3d.view_camera_offset
    nr3d.view_camera_zoom = pr3d.view_camera_zoom

    # TODO is there a better way? 90deg, 180 deg is culling here
    nr3d.view_matrix = copy.copy(pr3d.view_matrix)
    if nr3d.is_orthographic_side_view:
        tools.setView(nextArea, pr3d.view_rotation)
        nr3d.view_rotation = pr3d.view_rotation

    nr3d.view_location = pr3d.view_location

    # space 3d settings:
    tools.copy_settings(ps3d, ns3d)

    if bpy.context.scene.synch_settings.shading_type:
        ns3d.shading.type = ps3d.shading.type

    if bpy.context.scene.synch_settings.shading_settings:
        tools.copy_settings(ps3d.shading, ns3d.shading)

    if bpy.context.scene.synch_settings.overlays:
        tools.copy_settings(ps3d.overlay, ns3d.overlay)

    nr3d.update()
    nextArea.tag_redraw()

    _remember_sync_source(next1, nextArea)

# Triggers when window's workspace is changed
subscribe_to = bpy.types.Window, "workspace"
sinchmanager = sinchmanager_class()


@persistent
def load_handler(context, a):
    ws = bpy.context.workspace
    if ws.synch_active:
        _remember_sync_source(ws)
    else:
        sinchmanager.last_workspace = ws.name
    register_rna_sub()


def register_rna_sub():
    bpy.msgbus.clear_by_owner(sinchmanager)
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=sinchmanager,
        args=(bpy.context,),
        notify=update_workspace,
        options={"PERSISTENT"}
    )


class SYNCW_PT_link1(bpy.types.Panel):
    """You can toggle synchronization on specific workspaces"""
    bl_label = "Synchronize settings"
    bl_idname = "VIEW3D_SYNCW_PT_link1"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_context = "layout"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Synchronize 3D Views")
        layout.label(text="Off workspaces are skipped")
        for w in bpy.data.workspaces:
            layout.prop(w, 'synch_active', text=w.name)
        
        layout.label(text="Synchronize Settings")

        row = self.layout.row(align=True)
        row.prop(context.scene.synch_settings, "shading_type", text="",
                 toggle=True, icon='SHADING_TEXTURE')
        row.prop(context.scene.synch_settings, "shading_settings", text="",
                 toggle=True, icon='PREFERENCES')
        row.prop(context.scene.synch_settings, "overlays", text="",
                 toggle=True, icon='OVERLAY')


def setCurrent(self, context):
    """Update callback for global/workspace sync toggles."""
    if not context.scene.synch_settings.active:
        return None
    ws = context.workspace
    # Workspace sync off: do not replace the remembered sync-enabled source
    if not ws.synch_active:
        return None

    # Sync just enabled (or global sync turned on): pull from last enabled source
    if (sinchmanager.last_workspace
            and sinchmanager.last_workspace != ws.name
            and sinchmanager.last_workspace in bpy.data.workspaces):
        update_workspace(context)
    else:
        _remember_sync_source(ws)
    return None


def drawheader(self, context):
    bigestarea = get_biggest_area(context.workspace, "VIEW_3D", True)
    if bigestarea != context.area:
        return

    # Fallback if subscribe_rna did not fire on workspace switch
    if sinchmanager.last_workspace != context.workspace.name:
        update_workspace(context)

    # Only sync-enabled workspaces become the next copy source
    if context.scene.synch_settings.active and context.workspace.synch_active:
        sinchmanager.last_area = context.area

    # toggle & popover.
    row = self.layout.row(align=True)
    if context.scene.synch_settings.active:
        icon = 'LOCKVIEW_ON'
    else:
        icon = 'LOCKVIEW_OFF'
    row.prop(context.scene.synch_settings, "active", text="",
             toggle=True, icon=icon)
    sub = row.row(align=True)
    sub.active = context.scene.synch_settings.active
    sub.popover(
        SYNCW_PT_link1.bl_idname,
        text='',
        text_ctxt='',
        icon='NONE',
        icon_value=0
    )


class SyncSettings(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(
        name="Toggle synchronization",
        default=True,
        update=setCurrent)
    shading_type: bpy.props.BoolProperty(
        name="Synchronize also shading type",
        default=False)
    shading_settings: bpy.props.BoolProperty(
        name="Synchronize also shading settings",
        default=False)
    overlays: bpy.props.BoolProperty(
        name="Synchronize also overlays",
        default=False)


classes = (SYNCW_PT_link1, SyncSettings)


def register():
    bpy.types.WorkSpace.synch_active = bpy.props.BoolProperty(
        name="Toggle synchronization for the workspace",
        default=True,
        update=setCurrent
    )
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.synch_settings = bpy.props.PointerProperty(
        type=SyncSettings
    )
    bpy.app.handlers.load_post.append(load_handler)
    register_rna_sub()
    if hasattr(bpy.types, 'VIEW3D_HT_header'):
        bpy.types.VIEW3D_HT_header.append(drawheader)
    else:
        for pt in bpy.types.Header.__subclasses__():
            if pt.__name__ == "VIEW3D_HT_header":
                break
        pt.append(drawheader)


def unregister():
    bpy.app.handlers.load_post.remove(load_handler)
    bpy.msgbus.clear_by_owner(sinchmanager)
    if hasattr(bpy.types, 'VIEW3D_HT_header'):
        bpy.types.VIEW3D_HT_header.remove(drawheader)
    else:
        for pt in bpy.types.Header.__subclasses__():
            if pt.__name__ == "VIEW3D_HT_header":
                break
        pt.remove(drawheader)
    bpy.types.Scene.synch_settings = None
    bpy.types.WorkSpace.synch_active = None
    for cls in classes:
        bpy.utils.unregister_class(cls)