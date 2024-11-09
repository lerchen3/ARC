import json
import os
from typing import Any

import vision_prompting

DEFAULT_FILE_PATH = 'arc-agi_training_challenges.json'


class Task:
    def __init__(
            self,
            task_id: str,
            train_examples: list[dict[str, list[list[int]]]],
            test_examples: list[dict[str, list[list[int]]]],
            generate_images: bool = True
    ):
        """
        Initialize a Task instance.

        Parameters
        ----------
        task_id: str
            The ID of the task
        train_examples: list[dict[str, list[list[int]]]]
            The training examples for the task. Each example is a dictionary with
            keys 'input' and 'output', containing a 2d list of integers 
        test_examples: list[dict[str, list[list[int]]]]
            The test examples for the task. Each example is a dictionary with
            keys 'input' and 'output', containing a 2d list of integers
        generate_images: bool
            Whether to generate images for the task
        """
        self.task_id = task_id
        self.train_examples = train_examples
        self.test_examples = test_examples
        self.examples_with_images = None
        if generate_images:
            self.generate_example_images()

    def generate_example_images(self, image_dir: str = 'task_images') -> None:
        """Generate and store images for all training examples."""
        if self.examples_with_images is not None:
            return

        self.examples_with_images = []

        # Ensure the images directory exists
        os.makedirs(image_dir, exist_ok=True)

        for idx, example in enumerate(self.train_examples):
            image_filename = f"{image_dir}/{self.task_id}_{idx+1}.png"

            # Create the image representing the transformation
            base64_image = vision_prompting.create_transformation_image(
                example['input'],
                example['output'],
                save_location=image_filename,
                return_base64=True
            )

            # Store the example with its image
            example_with_image = {
                'input': example['input'],
                'output': example['output'],
                'base64_image': base64_image
            }
            self.examples_with_images.append(example_with_image)

    @property
    def num_examples(self) -> int:
        """Return the number of training examples."""
        return len(self.train_examples)

    @classmethod
    def from_dict(
            cls,
            task_id: str,
            task_data: dict[str, list[list[int]]],
            generate_images: bool = True
    ) -> 'Task':
        """Create a Task instance from a dictionary representation."""
        return cls(task_id, task_data['train'], task_data['test'], generate_images)


class TaskDatasetInstance:
    def __init__(self, file_path: str = DEFAULT_FILE_PATH):
        with open(file_path, 'r') as f:
            self.tasks: dict[str, dict[str, list[list[int]]]] = json.load(f)

    def get_task(self, task_id: str, generate_images: bool = True) -> 'Task':
        return Task.from_dict(task_id, self.tasks[task_id], generate_images)

    def keys(self) -> list[str]:
        return list(self.tasks.keys())


# Cache datasets

all_datasets = {}


def TaskDataset(file_path: str) -> TaskDatasetInstance:
    if file_path not in all_datasets:
        all_datasets[file_path] = TaskDatasetInstance(file_path)
    return all_datasets[file_path]


def get_task(file_path: str, task_id: str, generate_images: bool = True) -> Task:
    return TaskDataset(file_path).get_task(task_id, generate_images)
