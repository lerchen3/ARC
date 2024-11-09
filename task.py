import json
import os
from typing import Any, Dict, List

import vision_prompting

DEFAULT_FILE_PATH = 'arc-agi_training_challenges.json'


class Task:
    def __init__(self, task_id: str, train_examples: List[Dict[str, Any]], generate_images: bool = True):
        """
        Initialize a Task instance.

        Parameters
        ----------
        task_id: str
            The ID of the task
        train_examples: List[Dict[str, Any]]
            The training examples for the task
        generate_images: bool
            Whether to generate images for the task
        """
        self.task_id = task_id
        self.train_examples = train_examples
        self.examples_with_images = []
        if generate_images:
            self.generate_example_images()

    def generate_example_images(self, image_dir: str = 'task_images') -> None:
        """Generate and store images for all training examples."""
        # Ensure the images directory exists
        os.makedirs(image_dir, exist_ok=True)

        for idx, example in enumerate(self.train_examples):
            image_filename = f"{image_dir}/{self.task_id}_{idx+1}.png"

            # Create the image representing the transformation
            base64_image = vision_prompting.create_transformation_image(
                example['input'],
                example['output'],
                save_location=image_filename
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
    def from_dict(cls, task_id: str, task_data: Dict[str, Any]) -> 'Task':
        """Create a Task instance from a dictionary representation."""
        return cls(task_id, task_data['train'])


class TaskDataset:
    def __init__(self, file_path: str = DEFAULT_FILE_PATH):
        with open(file_path, 'r') as f:
            self.tasks = json.load(f)

    def get_task(self, task_id: str) -> 'Task':
        return Task.from_dict(task_id, self.tasks[task_id])

    def keys(self) -> list[str]:
        return list(self.tasks.keys())
