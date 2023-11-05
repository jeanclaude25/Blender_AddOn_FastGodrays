bl_info = {
    "name": "Fast Godrays",
    "author": "Jeanclaude Stephane",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > My Screen Space Panel",
    "description": "faking godrays by automatising the sunbeams nodes",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy
from bpy.props import PointerProperty, StringProperty
import mathutils
from bpy_extras.view3d_utils import location_3d_to_region_2d


# ------------------------------------------------------------------------
#    objects selection
# ------------------------------------------------------------------------
def update_func(self, context):
    # This function will be called when the property is updated,
    # allowing you to perform any updates necessary based on the new value.
    pass

class FastGodraysProperties(bpy.types.PropertyGroup):
    camera: bpy.props.PointerProperty(
        name="Camera",
        type=bpy.types.Object,
        description="Select a camera",
        update=update_func
    )
    light_source: bpy.props.PointerProperty(
        name="Light Source",
        type=bpy.types.Object,
        description="Select a light source",
        update=update_func
    )
    screen_x: bpy.props.FloatProperty()
    screen_y: bpy.props.FloatProperty()


# ------------------------------------------------------------------------
#    Render one single image
# ------------------------------------------------------------------------
class MakeOneRender(bpy.types.Operator):
    """Make_One_Render"""
    bl_idname = "do_render_image.id"
    bl_label = "do_render_image_label"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        #if apply sunBeams, apply sunBeams.
        bpy.ops.set_sunbeams_node.id('INVOKE_DEFAULT')
        #if apply Ellipse, apply Ellipse
        bpy.ops.set_ellipse_mask.id('INVOKE_DEFAULT')
        #Dorender
        bpy.ops.render.render(write_still=True)
        print("Make one single render")
        return {'FINISHED'}
    

# ------------------------------------------------------------------------
#    Render the whole timeline
# ------------------------------------------------------------------------
class MakeAnimation(bpy.types.Operator):
    """Make_Anim"""
    bl_idname = "do_animation.id"
    bl_label = "do_animation_label"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        startValue = bpy.data.scenes["Scene"].frame_start
        endValue = bpy.data.scenes["Scene"].frame_end
        print("Do animation between ", startValue, " and ", endValue)
        bpy.data.scenes["Scene"].frame_current = startValue
        
        #boucle for entre start value et endValue
        for frame in range(startValue, endValue + 1):
            bpy.context.scene.frame_set(frame)
            print(f"Rendering frame {frame}...")
            original_filepath = bpy.context.scene.render.filepath  # Save the original filepath
            bpy.context.scene.render.filepath = f"{original_filepath}{frame:04d}.png"
            bpy.ops.do_render_image.id('INVOKE_DEFAULT')
            bpy.context.scene.render.filepath = original_filepath
            
        
        
        return {'FINISHED'}
  
# ------------------------------------------------------------------------
#    Update SunBeams Node
# ------------------------------------------------------------------------
class UpdateSunBeamsNode(bpy.types.Operator):
    """Update_sunBeams_Node"""
    bl_idname = "set_sunbeams_node.id"
    bl_label = "set_sunbeams_node_label"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Invoke ScreenSpaceCoord to get the screen space coordinate
        bpy.ops.get_screen_space.id('INVOKE_DEFAULT')

        # Access the stored screen space coordinates
        screen_x = context.scene.fast_godrays_props.screen_x
        screen_y = context.scene.fast_godrays_props.screen_y
        
        comp_node_tree = bpy.context.scene.node_tree
        for node in comp_node_tree.nodes:
            if node.type == 'SUNBEAMS':
                node.source[0] = context.scene.fast_godrays_props.screen_x
                node.source[1] = context.scene.fast_godrays_props.screen_y
                
                break
        print("apply SunBeams value ", context.scene.fast_godrays_props.screen_x, context.scene.fast_godrays_props.screen_y)
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Update Ellipse Mask
# ------------------------------------------------------------------------
class UpdateEllipseMask(bpy.types.Operator):
    """Update_ellipseMask"""
    bl_idname = "set_ellipse_mask.id"
    bl_label = "set_ellipse_mask_label"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Invoke ScreenSpaceCoord to get the screen space coordinate
        bpy.ops.get_screen_space.id('INVOKE_DEFAULT')

        # Access the stored screen space coordinates
        screen_x = context.scene.fast_godrays_props.screen_x / 2.5
        screen_y = context.scene.fast_godrays_props.screen_y / 2.5
        
        comp_node_tree = bpy.context.scene.node_tree
        for node in comp_node_tree.nodes:
            if node.type == 'ELLIPSEMASK':
                node.x = screen_x
                node.y = screen_y
                break
        print("apply Ellipse Mask value ", screen_x, screen_y)
        return {'FINISHED'}
    
# ------------------------------------------------------------------------
#    translate cam location to 2d coordinate
# ------------------------------------------------------------------------
class ScreenSpaceCoord(bpy.types.Operator):
    """get ScreenSpaceCoord"""
    bl_idname = "get_screen_space.id"
    bl_label = "getScreenSpace_label"
    bl_options = {'REGISTER', 'UNDO'}
    
    @staticmethod
    def find_3d_view_space():
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        return space.region_3d
        return None

    def execute(self, context):
        
        fast_godrays_props = context.scene.fast_godrays_props
        camera = fast_godrays_props.camera
        target = fast_godrays_props.light_source
        
        # Make sure the camera and target are set by the user
        if not camera or not target:
            self.report({'ERROR'}, "Camera and/or Light Source not set.")
            return {'CANCELLED'}
        
        region = bpy.context.region
        rv3d = ScreenSpaceCoord.find_3d_view_space()
        
        if rv3d is None:
            self.report({'ERROR'}, "3D View Space not found.")
            return {'CANCELLED'}
        
        obj_location = target.location
        screen_coords = location_3d_to_region_2d(region, rv3d, obj_location)
        if screen_coords is not None:
            # Normaliser les coordonnées pour les faire varier entre 0 et 1
            correction = (0.0, 0.02)
            context.scene.fast_godrays_props.screen_x = (screen_coords.x / region.width)+correction[0]
            context.scene.fast_godrays_props.screen_y = (screen_coords.y / region.height)+correction[1]
            normalized_coords = (
                (screen_coords.x / region.width)+correction[0],
                (screen_coords.y / region.height)+correction[1])
            print("normalized_coords: ", normalized_coords)
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Menu
# ------------------------------------------------------------------------
class FASTGODRAYS_PT_SystemPanel(bpy.types.Panel):
    """Instance to emptys"""
    bl_label = "Fast Godrays"
    bl_idname = "FASTGODRAYS_PT_system_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fast Godrays" 
    
    def draw(self, context):
        
        layout = self.layout
        fast_godrays_props = context.scene.fast_godrays_props
        
        layout.prop(fast_godrays_props, "camera", text="Camera")
        layout.prop(fast_godrays_props, "light_source", text="Light Source")

        split = layout.split()
        
        row = layout.row()
        
        split = layout.split()
        
        row = layout.row()
        col = split.column(align=True)
        col.label(text="fast Godrays")
        row = layout.row()
        row.operator("set_sunbeams_node.id", text="Apply SunBeams value")
        row = layout.row()
        row.operator("set_ellipse_mask.id", text="Apply Ellipse Mask value")
        row = layout.row()
        row.operator("do_render_image.id", text="Render Image")
        row = layout.row()
        row.operator("do_animation.id", text="Render Animation")
        row = layout.row()
        
        
def register():
    #register objects selection
    bpy.utils.register_class(FastGodraysProperties)
    bpy.types.Scene.fast_godrays_props = bpy.props.PointerProperty(type=FastGodraysProperties)
    #register others
    bpy.utils.register_class(MakeAnimation)
    bpy.utils.register_class(MakeOneRender)
    bpy.utils.register_class(UpdateSunBeamsNode)
    bpy.utils.register_class(UpdateEllipseMask)
    bpy.utils.register_class(ScreenSpaceCoord)
    bpy.utils.register_class(FASTGODRAYS_PT_SystemPanel)
    
def unregister():
    bpy.utils.unregister_class(FastGodraysProperties)
    del bpy.types.Scene.fast_godrays_props
    
    bpy.utils.unregister_class(MakeAnimation)
    bpy.utils.unregister_class(MakeOneRender)
    bpy.utils.unregister_class(UpdateSunBeamsNode)
    bpy.utils.unregister_class(UpdateEllipseMask)
    bpy.utils.unregister_class(ScreenSpaceCoord)
    bpy.utils.unregister_class(FASTGODRAYS_PT_SystemPanel)

if __name__ == "__main__":
    register()