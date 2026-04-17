const countBy = (array, checkFunction) => {
  return array.reduce((count, element) => {
    return checkFunction(element) ? count + 1 : count;
  }, 0);
};

const checkExamples = (
  examples,
  labelset,
  dataset,
  dataset_config,
  analyser_type,
  analyser_format,
  onFail,
  onWarning,
  model_source,
) => {
  let labelled_examples = [];
  let labelled_examples_ref = [];
  let unlabelled_examples_ref = [];
  let unlabelled_examples = [];
  let unlabelled_positions = [];
  let non_example_labels = [];
  let pos_non_example_labels = [];
  let neg_non_example_labels = [];

  if (examples !== undefined && examples.length > 0) {
    labelled_examples = labelset.labels.filter(({ item_id }) => examples.includes(item_id));
    labelled_examples = labelled_examples.filter((label) => label !== "" && label != null);
    labelled_examples_ref = labelled_examples.map((a) => a.item_id);
    unlabelled_examples_ref = examples.filter((item_id) => !labelled_examples_ref.includes(item_id));
    unlabelled_examples = dataset.artworks.filter(({ _id }) => unlabelled_examples_ref.includes(_id));
    unlabelled_positions = unlabelled_examples.map((a) => a.position);
    non_example_labels = labelset.labels.filter(({ item_id }) => !examples.includes(item_id));
    non_example_labels = non_example_labels.filter((label) => label.toString().length > 0);
    if (analyser_type === "binary") {
      pos_non_example_labels = non_example_labels.map((label) => {
        return label.value.toString() === "1";
      });
      neg_non_example_labels = non_example_labels.map((label) => {
        return label.value.toString() === "0";
      });
    }
  }

  if (labelset.labels.length < 10) {
    onFail("Please label at least 10 items.");
    return {
      message: "Please label at least 10 items.",
      result: false,
    };
  } else if (examples.length === 0) {
    if (analyser_format === "text") {
      onFail("No examples selected. Please select at least 5 labelled examples.");
      return {
        message: "No examples selected. Please select at least 5 labelled examples.",
        result: false,
      };
    } else if (analyser_format.includes("image")) {
      onFail("No examples selected. Please select up to 5 labelled examples.");
      return {
        message: "No examples selected. Please select up to 5 labelled examples.",
        result: false,
      };
    }
  } else if (examples.length < 5 && analyser_format === "text") {
    onFail("Not enough examples selected. Please select at least 5 labelled examples.");
    return {
      message: "Not enough examples selected. Please select at least 5 labelled examples.",
      result: false,
    };
  } else if (examples.length > 5 && analyser_format.includes("image")) {
    onFail("Too many examples selected. Please select up to 5 labelled examples.");
    return {
      message: "Too many examples selected. Please select up to 5 labelled examples.",
      result: false,
    };
  } else if (unlabelled_examples.length !== 0) {
    onFail(`Please label all unlabelled examples (order number: ${unlabelled_positions})`);
    return {
      message: `Please label all unlabelled examples (${unlabelled_positions})`,
      result: false,
    };
  } else if (non_example_labels.length === 0) {
    onFail("Please exclude at least one labelled item from your selected examples.");
    return {
      message: "Please exclude at least one labelled item from your selected examples.",
      result: false,
    };
  }

  if (analyser_type === "binary") {
    if (pos_non_example_labels.length === 0) {
      onWarning("Before moving to review, please exclude at least one positively labelled item from your selected examples.");
      return {
        message:
          "Before moving to review, please exclude at least one positively labelled item from your selected examples.",
        result: true,
      };
    } else if (countBy(labelled_examples, (label) => label.value.toString() === "1") < 3) {
      onWarning("To improve results, try selecting at least 3 examples with positive labels.");
      return {
        message: "To improve results, try selecting at least 3 examples with positive labels.",
        result: true,
      };
    } else if (countBy(labelled_examples, (label) => label.value.toString() === "0") < 2) {
      onWarning("To improve results, try selecting at least 2 examples with negative labels.");
      return {
        message: "To improve results, try selecting at least 2 examples with negative labels.",
        result: true,
      };
    }
  } else if (analyser_type === "score") {
    // For score models, use binary labels (positive/negative) for training examples.
    if (countBy(labelled_examples, (label) => label.value.toString() === "0") / labelled_examples.length < 0.4) {
      onWarning("To improve results, try selecting more negative examples.");
      return {
        message: "To improve results, try selecting more negative examples.",
        result: true,
      };
    } else if (countBy(labelled_examples, (label) => label.value.toString() === "1") / labelled_examples.length < 0.4) {
      onWarning("To improve results, try selecting more positive examples.");
      return {
        message: "To improve results, try selecting more positive examples.",
        result: true,
      };
    }
  }

  onWarning("");
  onFail("");
  return {
    message: "",
    result: true,
  };
};

const checkSample = (sample, examples, labelset, onFail, onWarning, statusExists = false) => {
  let sample_items_labels = [];
  let labelled_sample_items = [];
  let non_example_labelled_sample_items = [];
  let example_labelled_sample_items = [];
  let non_example_labels = [];

  if (sample !== undefined && sample.length > 0) {
    sample_items_labels = labelset.labels.filter(({ item_id }) => sample.includes(item_id));
    sample_items_labels = sample_items_labels.filter((label) => label !== "" && label != null);
    labelled_sample_items = sample_items_labels.map((a) => a.item_id);
    non_example_labelled_sample_items = labelled_sample_items.filter((item_id) => !examples.includes(item_id));
    example_labelled_sample_items = labelled_sample_items.filter((item_id) => examples.includes(item_id));
    non_example_labels = labelset.labels.filter(({ item_id }) => !examples.includes(item_id));
    non_example_labels = non_example_labels.filter((label) => label.toString().length > 0);
  }

  if (sample.length < 3) {
    onFail("Please select at least 3 labelled items for your sample");
    return false;
  }

  if (labelled_sample_items.length < 3 && non_example_labels.length >= 3) {
    onFail("Please select at least 3 labelled items for your sample");
    return false;
  }

  if (labelled_sample_items.length - example_labelled_sample_items.length <= 2) {
    onWarning("Before moving to review, please include at least 3 labelled items in your sample that are not examples");
    return true;
  }

  if (!statusExists) {
    onWarning("");
    onFail("");
  }

  return true;
};

export { countBy, checkExamples, checkSample };
