#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
import random
import unittest

from mlos.Spaces.Hypergrids import SimpleHypergrid
import mlos.Spaces.Dimensions.DimensionCalculator
from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension
from mlos.Spaces.Dimensions.DiscreteDimension import DiscreteDimension
from mlos.Spaces.Dimensions.OrdinalDimension import OrdinalDimension
from mlos.Spaces.Dimensions.CategoricalDimension import CategoricalDimension
from mlos.Spaces.Point import Point

from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonDecoder
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonEncoder


class TestHierarchicalSpaces(unittest.TestCase):

    def setUp(self):
        self.original_root_communication_channel_parameter_space = SimpleHypergrid(
            name='communication_channel_parameter_space',
            dimensions=[
                DiscreteDimension(name='num_readers', min=1, max=64),
                DiscreteDimension(name='log2_buffer_size', min=10, max=24),
                CategoricalDimension(name='use_emergency_buffer', values=[True, False])
            ]
        )

        self.original_emergency_buffer_settings = SimpleHypergrid(
            name='emergency_buffer_config',
            dimensions=[
                DiscreteDimension(name='log2_emergency_buffer_size', min=0, max=16),
                CategoricalDimension(name='use_colors', values=[True, False])
            ]
        )

        self.original_emergency_buffer_color = SimpleHypergrid(
            name='emergency_buffer_color',
            dimensions=[
                CategoricalDimension(name='color', values=['Maroon', 'Crimson', 'Tanager'])
            ]
        )

        self.original_emergency_buffer_settings_with_color = self.original_emergency_buffer_settings.join(
            subgrid=self.original_emergency_buffer_color,
            on_external_dimension=CategoricalDimension(name='use_colors', values=[True])
        )

        self.original_hierarchical_settings = self.original_root_communication_channel_parameter_space.join(
            subgrid=self.original_emergency_buffer_settings_with_color,
            on_external_dimension=CategoricalDimension(name='use_emergency_buffer', values=[True]),
        )

        self.root_communication_channel_parameter_space = json.loads(json.dumps(self.original_root_communication_channel_parameter_space, cls=HypergridJsonEncoder), cls=HypergridJsonDecoder)
        self.emergency_buffer_settings = json.loads(json.dumps(self.original_emergency_buffer_settings, cls=HypergridJsonEncoder), cls=HypergridJsonDecoder)
        self.emergency_buffer_color = json.loads(json.dumps(self.original_emergency_buffer_color, cls=HypergridJsonEncoder), cls=HypergridJsonDecoder)
        self.emergency_buffer_settings_with_color = json.loads(json.dumps(self.original_emergency_buffer_settings_with_color, cls=HypergridJsonEncoder), cls=HypergridJsonDecoder)
        self.hierarchical_settings = json.loads(json.dumps(self.original_hierarchical_settings, cls=HypergridJsonEncoder), cls=HypergridJsonDecoder)


    def test_hierachical_spaces(self):

        valid_config_no_emergency_buffer = Point(
            num_readers=1,
            log2_buffer_size=10,
            use_emergency_buffer=False
        )

        valid_config_with_emergency_buffer = Point(
            num_readers=1,
            log2_buffer_size=10,
            use_emergency_buffer=True,
            emergency_buffer_config = Point(
                log2_emergency_buffer_size=2,
                use_colors=False
            )
        )

        valid_config_with_emergency_buffer_colors = Point(
            num_readers=1,
            log2_buffer_size=10,
            use_emergency_buffer=True,
            emergency_buffer_config = Point(
                log2_emergency_buffer_size=2,
                use_colors=True,
                emergency_buffer_color = Point(color='Crimson')
            )
        )

        valid_config_with_emergency_buffer_and_redundant_coordinates = Point(
            num_readers=1,
            log2_buffer_size=10,
            use_emergency_buffer=False,
            log2_emergency_buffer_size=2
        )

        another_invalid_config_with_emergency_buffer = Point(
            num_readers=1,
            log2_buffer_size=10,
            use_emergency_buffer=True
        )

        yet_another_invalid_config_with_emergency_buffer = Point(
            num_readers=1,
            log2_buffer_size=10,
            use_emergency_buffer=True,
            emergency_buffer_config = Point(
                log2_emergency_buffer_size=40
            )
        )

        self.assertTrue(valid_config_no_emergency_buffer in self.root_communication_channel_parameter_space)
        self.assertTrue(valid_config_no_emergency_buffer in self.hierarchical_settings)
        self.assertTrue(valid_config_with_emergency_buffer in self.hierarchical_settings)
        self.assertTrue(valid_config_with_emergency_buffer_colors in self.hierarchical_settings)
        self.assertTrue(valid_config_with_emergency_buffer_and_redundant_coordinates in self.hierarchical_settings)
        self.assertTrue(another_invalid_config_with_emergency_buffer not in self.hierarchical_settings)
        self.assertTrue(yet_another_invalid_config_with_emergency_buffer not in self.hierarchical_settings)

    def test_generating_random_configs(self):
        used_emergency_buffer = False
        used_color = False
        used_crimson = False

        # Let's seed it to make sure we get consistent test results
        random_state = random.Random()
        random_state.seed(1)
        self.hierarchical_settings.random_state = random_state

        for _ in range(100):
            random_config = self.hierarchical_settings.random()
            self.assertTrue(random_config in self.hierarchical_settings)
            used_emergency_buffer = used_emergency_buffer or random_config['use_emergency_buffer']
            if random_config['use_emergency_buffer']:
                used_color = used_color or random_config['emergency_buffer_config']['use_colors']
                if random_config['emergency_buffer_config']['use_colors']:
                    used_crimson = used_crimson or (random_config['emergency_buffer_config']['emergency_buffer_color']['color'] == 'Crimson')
        self.assertTrue(used_emergency_buffer)
        self.assertTrue(used_color)
        self.assertTrue(used_crimson)

    def test_reseeding_random_state(self):
        previous_iteration_first_pass_points = None

        for i in range(10):
            # let's seed the grid for the first time
            random_state = random.Random()
            random_state.seed(i)
            self.hierarchical_settings.random_state = random_state

            first_pass_points = [self.hierarchical_settings.random() for _ in range(100)]

            # let's do it again
            random_state = random.Random()
            random_state.seed(i)
            self.hierarchical_settings.random_state = random_state

            second_pass_points = [self.hierarchical_settings.random() for _ in range(100)]

            for first_pass_point, second_pass_point in zip(first_pass_points, second_pass_points):
                self.assertTrue(first_pass_point == second_pass_point)

            if previous_iteration_first_pass_points is not None:
                # Let's make sure we keep changing the points
                self.assertTrue(
                    any(
                        previous != current
                        for previous, current
                        in zip(previous_iteration_first_pass_points, first_pass_points)
                    )
                )
            previous_iteration_first_pass_points = first_pass_points

    def test_printing_serialized_configs(self):
        print("-------------------------------------------------------------------------------------------------------")
        print(json.dumps(self.original_root_communication_channel_parameter_space, cls=HypergridJsonEncoder, indent=2))
        print("-------------------------------------------------------------------------------------------------------")
        print(json.dumps(self.original_emergency_buffer_settings, cls=HypergridJsonEncoder, indent=2))
        print("-------------------------------------------------------------------------------------------------------")
        print(json.dumps(self.original_emergency_buffer_color, cls=HypergridJsonEncoder, indent=2))
        print("-------------------------------------------------------------------------------------------------------")
        print(json.dumps(self.original_emergency_buffer_settings_with_color, cls=HypergridJsonEncoder, indent=2))
        print("-------------------------------------------------------------------------------------------------------")
        print(json.dumps(self.original_hierarchical_settings, cls=HypergridJsonEncoder, indent=2))
        print("-------------------------------------------------------------------------------------------------------")

