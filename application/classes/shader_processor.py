
import moderngl
import numpy as np
from PIL import Image
from abc import ABC, abstractmethod


# ------------------------
# Vertex shader source code
# ------------------------
vertex_shader_source = '''
#version 330 core
in vec2 in_vert;
in vec2 in_uv;
out vec2 vUv;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    vUv = in_uv;
}
'''


class ShaderProcessorBase(ABC):
    """
    Base class for GPU shader processing of images.

    :raise TypeError: If the input image is not a PIL.Image or numpy.ndarray.
    """

    # ------------------------
    # Initialization
    # ------------------------
    def __init__(self):
        self.ctx = moderngl.create_standalone_context()
        self.prog = self.ctx.program(
            vertex_shader=vertex_shader_source,
            fragment_shader=self.fragment_shader()
        )
        # Vertex buffer for a full-screen quad
        self.vbo = self.ctx.buffer(np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4').tobytes())
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert', 'in_uv')

        # GPU resources
        self.texture = None
        self.fbo = None
        self.out_tex = None
        self.size = None

    # ------------------------
    # Abstract methods
    # ------------------------
    @abstractmethod
    def fragment_shader(self) -> str:
        """Return the fragment shader source code as a string."""
        pass

    @abstractmethod
    def set_uniforms(self, **kwargs):
        """Set custom shader uniforms for processing."""
        pass

    # ------------------------
    # Internal resource management
    # ------------------------
    def _ensure_resources(self, w: int, h: int):
        """
        Ensure GPU textures and framebuffer exist with the correct size.

        :param w: Width of the image.
        :param h: Height of the image.
        """
        if self.size != (w, h):
            self.texture = self.ctx.texture((w, h), 4)
            self.out_tex = self.ctx.texture((w, h), 4)
            self.fbo = self.ctx.framebuffer(color_attachments=[self.out_tex])
            self.size = (w, h)

    # ------------------------
    # Main processing
    # ------------------------
    def process(self, image, **kwargs) -> np.ndarray:
        """
        Apply the shader to an input image.

        :param image: Input image, either PIL.Image or numpy.ndarray.
        :param kwargs: Additional uniform parameters for the shader.
        :return: Processed image as an RGBA numpy.ndarray.
        :raise TypeError: If the input is not a PIL.Image or numpy.ndarray.
        """
        # Convert input to RGBA numpy array
        if isinstance(image, Image.Image):
            image = image.convert('RGBA')
            img_data = np.array(image, dtype=np.uint8)
        elif isinstance(image, np.ndarray):
            if image.shape[-1] == 3:
                # Add alpha channel if missing
                alpha = np.full((image.shape[0], image.shape[1], 1), 255, dtype=np.uint8)
                img_data = np.concatenate([image, alpha], axis=-1)
            else:
                img_data = image.astype(np.uint8)
        else:
            raise TypeError("ShaderProcessorBase.process() accepts only PIL.Image or numpy.ndarray")

        h, w = img_data.shape[:2]

        # Ensure GPU resources match image size
        self._ensure_resources(w, h)

        # Upload texture and bind
        self.texture.write(img_data.tobytes())
        self.texture.use(location=0)

        # Set shader uniforms
        self.prog['tDiffuse'].value = 0
        self.set_uniforms(**kwargs)

        # Render to framebuffer
        self.fbo.use()
        self.fbo.clear(0.0, 0.0, 0.0, 0.0)
        self.vao.render()

        # Read processed image from GPU
        data = self.fbo.read(components=4, alignment=1)
        result = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4))

        return result
