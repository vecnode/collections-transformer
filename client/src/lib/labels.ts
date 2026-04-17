import type { AnalyserType } from "@/types";

const binary_val_to_label = (val: string | number | boolean): "positive" | "negative" | "" => {
  if (val.toString() == "1") {
    return "positive";
  }
  if (val.toString() == "0") {
    return "negative";
  }
  return "";
};

const example_val_to_label = (val: string | number | boolean): "●" | "----" | "" => {
  if (val == 1) {
    return "●";
  }
  if (val == 0) {
    return "----";
  }
  return "";
};

const formatAnalyserType = (analyser_type: AnalyserType): string => {
  if (analyser_type == "binary") {
    return "Classify True or False";
  }
  if (analyser_type == "score") {
    return "Score (0-5)";
  }
  if (analyser_type == "opinion") {
    return "Opinion";
  }
  if (analyser_type == "keywords") {
    return "Count keywords";
  }
  return "";
};

export { binary_val_to_label, example_val_to_label, formatAnalyserType };
