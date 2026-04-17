const checkChanges = (version, previousVersion) => {
  if (previousVersion) {
    const changes = [];

    if (version.task_description !== previousVersion.task_description) {
      changes.push("task description");
    }
    if (version.labelling_guide !== previousVersion.labelling_guide) {
      changes.push("labelling guide");
    }
    if (JSON.stringify(version.example_refs.sort()) !== JSON.stringify(previousVersion.example_refs.sort())) {
      changes.push("training examples");
    }
    if (JSON.stringify(version.sample_ids.sort()) !== JSON.stringify(previousVersion.sample_ids.sort())) {
      changes.push("test samples");
    }

    if (changes.length > 0) {
      return changes.join(", ");
    }
  }

  return undefined;
};

export { checkChanges };
