import os


class TaskSyncStorage:
    """Persist synchronized tasks in text format compatible with task parser."""

    def __init__(self, filename: str):
        self.filename = filename

    def update_file(self, tasks: list, customer_name: str, task_format: str):
        """Merge synchronized tasks with existing file while preserving non-customer lines."""
        final_content = []

        if os.path.exists(self.filename):
            with open(self.filename, encoding='utf-8') as file_obj:
                for line in file_obj.readlines():
                    if not line.startswith(f'{customer_name}:') or 'ASYNC' in line:
                        final_content.append(line)

        for task in sorted(tasks, key=lambda item: item.id):
            final_content.append(task.render(task_format))

        os.makedirs(os.path.dirname(os.path.abspath(self.filename)), exist_ok=True)
        with open(self.filename, 'w', encoding='utf-8') as file_obj:
            file_obj.writelines(final_content)
