import math
import unittest

import numpy as np

from library.utils.nfs6_sky_to_spherical import EYE_HEIGHT, is_nfs6_sky_archive, nfs6_sky_to_spherical
from library.utils.sky_spherical import OUT_HEIGHT, OUT_WIDTH, direction_to_pixel, output_directions

W, H = 256, 128


def ring(radius, y_bottom, y_top, sectors=32, u_turns=1.0):
    """Cylinder around the origin as the skyg.o meshes are: vertices, triangles, uvs (u along the turn, v down)"""
    vertices, uvs, triangles = [], [], []
    for i in range(sectors + 1):
        a = 2 * math.pi * i / sectors
        x, z = radius * math.cos(a), radius * math.sin(a)
        vertices += [(x, y_top, z), (x, y_bottom, z)]
        uvs += [(u_turns * i / sectors, 0.0), (u_turns * i / sectors, 1.0)]
        if i:
            b = 2 * i
            triangles += [(b - 2, b - 1, b), (b - 1, b + 1, b)]
    return vertices, triangles, uvs


def solid(color, alpha=255, size=4):
    texture = np.zeros((size, size, 4))
    texture[..., :3] = color
    texture[..., 3] = alpha
    return texture


class TestOutputLayout(unittest.TestCase):
    def test_centre_is_plus_x_and_right_is_minus_z(self):
        directions = output_directions(W, H)
        centre = directions[H // 2, W // 2]
        self.assertGreater(centre[0], 0.99)
        quarter_right = directions[H // 2, W // 2 + W // 4]
        self.assertLess(quarter_right[2], -0.99)
        quarter_left = directions[H // 2, W // 2 - W // 4]
        self.assertGreater(quarter_left[2], 0.99)
        self.assertGreater(directions[0, 0][1], 0.99)

    def test_direction_to_pixel(self):
        col, row = direction_to_pixel((0, 0, -1))
        self.assertAlmostEqual(col, OUT_WIDTH * 0.75)
        self.assertAlmostEqual(row, OUT_HEIGHT / 2)


class TestNfs6Sky(unittest.TestCase):
    def test_clear_colour_where_no_mesh(self):
        out = nfs6_sky_to_spherical([], clear_color=(1, 2, 3), width=W, height=H)
        self.assertEqual(out[0, 0].tolist(), [1, 2, 3, 255])

    def test_ring_at_eye_height_is_on_the_horizon(self):
        # a thin ring 12.4 above the model origin (the eye height) covers the middle rows only
        vertices, triangles, uvs = ring(1000, EYE_HEIGHT - 20, EYE_HEIGHT + 20)
        out = nfs6_sky_to_spherical(
            [(vertices, triangles, uvs, [], solid((255, 0, 0)))], clear_color=(0, 0, 0), width=W, height=H
        )
        self.assertEqual(out[H // 2, 10, 0], 255)
        self.assertEqual(out[H // 2 - 3, 10, 0], 0)
        self.assertEqual(out[H // 2 + 3, 10, 0], 0)

    def test_texture_coordinates_and_draw_order(self):
        # first mesh: left half of the texture red, right half green, once around; second: half transparent blue
        texture = np.zeros((4, 8, 4))
        texture[..., 3] = 255
        texture[:, :4, 0] = 255
        texture[:, 4:, 1] = 255
        band = ring(1000, -500, 500)
        overlay = ring(900, -100, 100)
        out = nfs6_sky_to_spherical(
            [(*band, [], texture), (*overlay, [], solid((0, 0, 255), alpha=128))],
            clear_color=(0, 0, 0),
            eye_height=0,
            width=W,
            height=H,
        )
        # u grows with the angle from +X towards +Z: +Z (a quarter left of the centre) is red, -Z is green
        self.assertEqual(out[H // 2 - 10, W // 4, 0], 255)
        self.assertEqual(out[H // 2 - 10, 3 * W // 4, 1], 255)
        blended = out[H // 2, W // 4]
        self.assertAlmostEqual(blended[2], 255 * 128 / 255, delta=1)
        self.assertAlmostEqual(blended[0], 255 * 127 / 255, delta=1)

    def test_vertex_colour_modulates(self):
        vertices, triangles, uvs = ring(1000, -500, 500)
        colors = [0x808080FF] * len(vertices)
        out = nfs6_sky_to_spherical(
            [(vertices, triangles, uvs, colors, solid((200, 200, 200)))], eye_height=0, width=W, height=H
        )
        self.assertAlmostEqual(out[H // 2, 0, 0], 200 * 0x80 / 255, delta=0.5)

    def test_sky_archive_ids(self):
        self.assertTrue(is_nfs6_sky_archive('games/nfs6/tracks/Alpine/persist.viv__children/4/item/data'))
        self.assertFalse(is_nfs6_sky_archive('games/nfs6/cars/a/car.viv__children/4/item/data'))
        self.assertFalse(is_nfs6_sky_archive(None))
