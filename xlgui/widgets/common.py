# Copyright (C) 2010 Adam Olsen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#
# The developers of the Exaile media player hereby grant permission
# for non-GPL compatible GStreamer and Exaile plugins to be used and
# distributed together with GStreamer and Exaile. This permission is
# above and beyond the permissions granted by the GPL license by which
# Exaile is covered. If you modify this code, you may extend this
# exception to your version of the code, but you are not obligated to
# do so. If you do not wish to do so, delete this exception statement
# from your version.

"""
    Shared GUI widgets
"""

import gio
import glib
import gobject
import gtk
from urllib2 import urlparse

from xl import (
    common,
    covers,
    playlist,
    settings,
    trax
)
from xlgui.guiutil import get_workarea_size
from xlgui import icons

class AttachedWindow(gtk.Window):
    """
        A window attachable to arbitrary widgets,
        follows the movement of its parent
    """
    __gsignals__ = {'show': 'override'}

    def __init__(self, parent):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.set_decorated(False)
        self.props.skip_taskbar_hint = True
        self.set_keep_above(True)

        self.realize()
        self.window.set_functions(gtk.gdk.FUNC_RESIZE) # Only allow resizing

        self.parent_widget = parent
        realize_id = self.parent_widget.connect('realize',
            self.on_parent_realize)
        self.parent_widget.set_data('%s_realize_id' % id(self),
            realize_id)

    def update_location(self):
        """
            Makes sure the window is
            always fully visible
        """
        workarea = gtk.gdk.Rectangle(0, 0, *get_workarea_size())
        parent = self.parent_widget.allocation
        toplevel_position = self.parent_widget.get_toplevel().get_position()
        # Use absolute screen position
        parent.x += toplevel_position[0]
        parent.y += toplevel_position[1]

        if workarea.width - parent.x < self.allocation.width:
            # Parent rightmost
            x = parent.x + parent.width - self.allocation.width
        else:
            # Parent leftmost
            x = parent.x

        if workarea.height - parent.y < self.allocation.height:
            # Parent at bottom
            y = parent.y - self.allocation.height
        else:
            # Parent at top
            y = parent.y + parent.height
        
        self.move(x, y)

    def do_show(self):
        """
            Updates the location upon show
        """
        gtk.Window.do_show(self)
        self.update_location()

    def on_parent_realize(self, parent):
        """
            Prepares the window to
            follow its parent window
        """
        realize_id = parent.get_data('%s_realize_id' % id(self))
        
        if realize_id is not None:
            parent.disconnect(realize_id)

        parent_window = parent.get_toplevel()
        parent_window.connect('configure-event',
            self.on_parent_window_configure_event)
        parent_window.connect('window-state-event',
            self.on_parent_window_state_event)

    def on_parent_window_configure_event(self, *e):
        """
            Handles movement of the topmost window
        """
        if self.props.visible:
            self.update_location()

    def on_parent_window_state_event(self, window, e):
        """
            Handles state changes of the topmost window
        """
        if e.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
            self.hide()

class AutoScrollTreeView(gtk.TreeView):
    """
        A TreeView which handles autoscrolling upon DnD operations
    """
    def __init__(self):
        gtk.TreeView.__init__(self)

        self._SCROLL_EDGE_SIZE = 15 # As in gtktreeview.c

        self.connect("drag-motion", self._on_drag_motion)
        self.connect("drag-leave", self._on_drag_leave)

    def _on_drag_motion(self, widget, context, x, y, timestamp):
        """
            Initiates automatic scrolling
        """
        if not self.get_data('autoscroll_timeout_id'):
            self.set_data('autoscroll_timeout_id',
                glib.timeout_add(50, self._on_autoscroll_timeout))

    def _on_drag_leave(self, widget, context, timestamp):
        """
            Stops automatic scrolling
        """
        autoscroll_timeout_id = self.get_data('autoscroll_timeout_id')
        
        if autoscroll_timeout_id:
            glib.source_remove(autoscroll_timeout_id)
            self.set_data('autoscroll_timeout_id', None)

    def _on_autoscroll_timeout(self):
        """
            Automatically scrolls during drag operations

            Adapted from gtk_tree_view_vertical_autoscroll() in gtktreeview.c
        """
        x, y, modifier = self.props.window.get_pointer()
        x, y = self.widget_to_tree_coords(x, y)
        visible_rect = self.get_visible_rect()
        # Calculate offset from the top edge
        offset = y - (visible_rect.y + 3 * self._SCROLL_EDGE_SIZE) # 3: Scroll faster upwards

        # Check if we are near the bottom edge instead
        if offset > 0:
            # Calculate offset based on the bottom edge
            offset = y - (visible_rect.y + visible_rect.height - 2 * self._SCROLL_EDGE_SIZE)

            # Skip if we are not near to top or bottom edge
            if offset < 0:
                return True

        vadjustment = self.get_vadjustment()
        vadjustment.value = common.clamp(
            vadjustment.value + offset,
            0,
            vadjustment.upper - vadjustment.page_size
        )
        self.set_vadjustment(vadjustment)

        return True

class DragTreeView(AutoScrollTreeView):
    """
        A TextView that does easy dragging/selecting/popup menu
    """
    targets = [("text/uri-list", 0, 0)]
    dragged_data = dict()

    def __init__(self, container, receive=True, source=True, drop_pos=None):
        """
            Initializes the tree and sets up the various callbacks
            :param container: The container to place the TreeView into
            :param receive: True if the TreeView should receive drag events
            :param source: True if the TreeView should send drag events
            :param drop_pos: Indicates where a drop operation should occur
                    w.r.t. existing entries: 'into', 'between', or None (both).
        """
        AutoScrollTreeView.__init__(self)
        self.container = container

        if source:
            self.drag_source_set(
                gtk.gdk.BUTTON1_MASK, self.targets,
                gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE)

        if receive:
            self.drop_pos = drop_pos
            self.drag_dest_set(gtk.DEST_DEFAULT_ALL, self.targets,
                gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_DEFAULT|
                gtk.gdk.ACTION_MOVE)
            self.connect('drag_data_received',
                self.container.drag_data_received)
            self.connect('drag_data_delete',
                self.container.drag_data_delete)
        self.receive = receive
        self.dragging = False
        self.show_cover_drag_icon = True
        self.connect('drag-begin', self.on_drag_begin)
        self.connect('drag-end', self.on_drag_end)
        self.connect('drag-motion', self.on_drag_motion)
        self.connect('button-release-event', self.on_button_release)
        self.connect('button-press-event', self.on_button_press)

        if source:
            self.connect('drag-data-get', self.container.drag_get_data)
            self.drag_source_set_icon_stock(gtk.STOCK_DND)

    def get_selected_tracks(self):
        """
            Returns the currently selected tracks (stub)
        """
        pass

    def on_drag_end(self, list, context):
        """
            Called when the dnd is ended
        """
        self.dragging = False
        self.unset_rows_drag_dest()
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, self.targets,
            gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE)

    def on_drag_begin(self, widget, context):
        """
            Sets the cover of dragged tracks as drag icon
        """
        self.dragging = True
        context.drag_abort(gtk.get_current_event_time())

        if self.get_selection().count_selected_rows() > 1:
            self.drag_source_set_icon_stock(gtk.STOCK_DND_MULTIPLE)
        else:
            self.drag_source_set_icon_stock(gtk.STOCK_DND)
        if self.show_cover_drag_icon:
            tracks = self.get_selected_tracks()
            self._on_drag_begin(widget, context, tracks)

    @common.threaded
    def _on_drag_begin(self, widget, context, tracks):
        """
            Async call counterpart to on_drag_begin, so that cover fetching
            doesn't block dragging.
        """
        cover_manager = covers.MANAGER
        width = height = settings.get_option('gui/cover_width', 100)

        if tracks:
            tracks = trax.util.sort_tracks(['album', 'tracknumber'], tracks)
            pixbuf = None
            first_pixbuf = None
            albums = []

            for track in tracks:
                album = track.get_tag_raw('album', join=True)
                if album not in albums:
                    image_data = cover_manager.get_cover(track,
                        set_only=True, use_default=True)
                    pixbuf = icons.MANAGER.pixbuf_from_data(
                        image_data, (width, height))

                    if first_pixbuf is None:
                        first_pixbuf = pixbuf
                    albums += [album]

                    if len(albums) >= 2:
                        break

            if pixbuf is not None:
                cover_pixbuf = pixbuf

                if len(albums) > 1:
                    # Create stacked-cover effect
                    cover_pixbuf = gtk.gdk.Pixbuf(
                        gtk.gdk.COLORSPACE_RGB,
                        True,
                        8,
                        width + 10, height + 10
                    )

                    fill_pixbuf = cover_pixbuf.subpixbuf(
                        0, 0, width + 10, height + 10)
                    fill_pixbuf.fill(0x00000000) # Fill with transparent background

                    fill_pixbuf = cover_pixbuf.subpixbuf(
                        0, 0, width, height)
                    fill_pixbuf.fill(0xccccccff)

                    if first_pixbuf != pixbuf:
                        pixbuf.copy_area(
                            0, 0, width, height,
                            cover_pixbuf,
                            5, 5
                        )
                    else:
                        fill_pixbuf = cover_pixbuf.subpixbuf(
                            5, 5, width, height)
                        fill_pixbuf.fill(0x999999ff)

                    first_pixbuf.copy_area(
                        0, 0, width, height,
                        cover_pixbuf,
                        10, 10
                    )

                glib.idle_add(self._set_drag_cover, context, cover_pixbuf)

    def _set_drag_cover(self, context, pixbuf):
        """
            Completes drag icon setup
        """
        context.set_icon_pixbuf(pixbuf, 0, 0)

    def on_drag_motion(self, treeview, context, x, y, timestamp):
        """
            Called when a row is dragged over this treeview
        """
        if not self.receive:
            return False
        self.enable_model_drag_dest(self.targets,
            gtk.gdk.ACTION_DEFAULT)
        if self.drop_pos is None:
            return False
        info = treeview.get_dest_row_at_pos(x, y)
        if not info:
            return False
        path, pos = info
        if self.drop_pos == 'into':
            # Only allow dropping into entries.
            if pos == gtk.TREE_VIEW_DROP_BEFORE:
                pos = gtk.TREE_VIEW_DROP_INTO_OR_BEFORE
            elif pos == gtk.TREE_VIEW_DROP_AFTER:
                pos = gtk.TREE_VIEW_DROP_INTO_OR_AFTER
        elif self.drop_pos == 'between':
            # Only allow dropping between entries.
            if pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
                pos = gtk.TREE_VIEW_DROP_BEFORE
            elif pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
                pos = gtk.TREE_VIEW_DROP_AFTER
        treeview.set_drag_dest_row(path, pos)
        context.drag_status(context.suggested_action, timestamp)
        return True

    def on_button_press(self, button, event):
        """
            The popup menu that is displayed when you right click in the
            playlist
        """
        selection = self.get_selection()
        (x, y) = event.get_coords()
        x = int(x)
        y = int(y)
        path = self.get_path_at_pos(x, y)

        if path:
            if event.button != 3:
                if event.type == gtk.gdk._2BUTTON_PRESS:
                    try:
                        return self.container.button_press(button, event)
                    except AttributeError:
                        pass

                if selection.count_selected_rows() <= 1:
                    return False
                else:
                    if selection.path_is_selected(path[0]):
                        if event.state & (gtk.gdk.SHIFT_MASK|gtk.gdk.CONTROL_MASK):
                            selection.unselect_path(path[0])
                        return True
                    elif not event.state & (gtk.gdk.SHIFT_MASK|gtk.gdk.CONTROL_MASK):
                        return True
                    return False

            if not selection.count_selected_rows():
                selection.select_path(path[0])
        try:
            return self.container.button_press(button, event)
        except AttributeError:
            pass

    def on_button_release(self, button, event):
        """
            Called when a button is released
        """
        if event.button != 1 or \
           self.dragging or \
           event.state & (gtk.gdk.SHIFT_MASK|gtk.gdk.CONTROL_MASK):
            self.dragging = False

            try:
                return self.container.button_release(button, event)
            except AttributeError:
                pass
        
        selection = self.get_selection()
        selection.unselect_all()

        path = self.get_path_at_pos(int(event.x), int(event.y))

        if not path:
            return False

        selection.select_path(path[0])

        try:
            return self.container.button_release(button, event)
        except AttributeError:
            pass

    #TODO maybe move this somewhere else? (along with _handle_unknown_drag_data)
    def get_drag_data(self, locs, compile_tracks = True, existing_tracks = []):
        """
            Handles the locations from drag data

            @param locs: locations we are dealing with (can
                be anything from a file to a folder)
            @param compile_tracks: if true any tracks in the playlists
                that are not found as tracks are added to the list of tracks
            @param existing_tracks: a list of tracks that have already
                been loaded from files (used to skip loading the dragged
                tracks from the filesystem)

            @returns: a 2 tuple in which the first part is a list of tracks
                and the second is a list of playlist (note: any files that are
                in a playlist are not added to the list of tracks, but a track could
                be both in as a found track and part of a playlist)
        """
        #TODO handle if they pass in existing tracks
        trs = []
        playlists = []
        for loc in locs:
            (found_tracks, found_playlist) = self._handle_unknown_drag_data(loc)
            trs.extend(found_tracks)
            playlists.extend(found_playlist)

        if compile_tracks:
            #Add any tracks in the playlist to the master list of tracks
            for playlist in playlists:
                for track in playlist.get_tracks():
                    if track not in trs:
                        trs.append(track)

        return (trs, playlists)

    def _handle_unknown_drag_data(self, loc):
        """
            Handles unknown drag data that has been recieved by
            drag_data_received.  Unknown drag data is classified as
            any loc (location) that is not in the collection of tracks
            (i.e. a new song, or a new playlist)

            @param loc:
                the location of the unknown drag data

            @returns: a 2 tuple in which the first part is a list of tracks
                and the second is a list of playlist
        """
        filetype = None
        info = urlparse.urlparse(loc)

        # don't use gio to test the filetype if it's a non-local file
        # (otherwise gio will try to connect to every remote url passed in and
        # cause the gui to hang)
        if info.scheme in ('file', ''):
            try:
                filetype = gio.File(loc).query_info(
                    'standard::type').get_file_type()
            except gio.Error:
                filetype = None

        if trax.is_valid_track(loc) or info.scheme not in ('file', ''):
            new_track = trax.Track(loc)
            return ([new_track],[])
        elif playlist.is_valid_playlist(loc):
            #User is dragging a playlist into the playlist list
            # so we add all of the songs in the playlist
            # to the list
            new_playlist = playlist.import_playlist(loc)
            return ([], [new_playlist])
        elif filetype == gio.FILE_TYPE_DIRECTORY:
            return (trax.get_tracks_from_uri(loc), [])
        else: #We don't know what they dropped
            return ([], [])

class ClickableCellRendererPixbuf(gtk.CellRendererPixbuf):
    """
        Custom :class:`gtk.CellRendererPixbuf` emitting
        an *clicked* signal upon activation of the pixbuf
    """
    __gsignals__ = {
        'clicked': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_BOOLEAN,
            (gobject.TYPE_PYOBJECT,),
            gobject.signal_accumulator_true_handled
        )
    }

    def __init__(self):
        gtk.CellRendererPixbuf.__init__(self)
        self.props.mode = gtk.CELL_RENDERER_MODE_ACTIVATABLE

    def do_activate(self, event, widget, path,
            background_area, cell_area, flags):
        """
            Emits the *clicked* signal
        """
        if event is None: # Keyboard activation
            return

        pixbuf_width = self.props.pixbuf.get_width()
        pixbuf_height = self.props.pixbuf.get_height()

        click_area = gtk.gdk.Rectangle(
            x=int(cell_area.x \
              + self.props.xpad \
              + self.props.xalign * cell_area.width \
              - pixbuf_width),
            y=int(cell_area.y \
              + self.props.ypad \
              + self.props.yalign * cell_area.height \
              - self.props.yalign * pixbuf_height),
            width=pixbuf_width,
            height=pixbuf_height
        )

        if click_area.x <= event.x <= click_area.x + click_area.width and \
           click_area.y <= event.y <= click_area.y + click_area.height:
            self.emit('clicked', path)

