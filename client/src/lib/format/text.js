const capitaliseFirstLetter = (string) => {
  return string.charAt(0).toUpperCase() + string.slice(1);
};

const parseObjIdString = (id_string) => {
  return id_string.replaceAll('"', "");
};

const formatAccuracy = (accuracy) => {
  const score = parseFloat(accuracy).toFixed(2);
  let rating = "";

  if (score <= 0.5) {
    rating = "Poor";
  } else if (score > 0.5 && score <= 0.7) {
    rating = "OK";
  } else if (score > 0.7 && score <= 0.8) {
    rating = "Good!";
  } else if (score > 0.8) {
    rating = "Excellent!";
  }

  const score_per = (score * 100).toFixed(0) + "%";
  return `${score_per} (${rating})`;
};

const getGrade = (target, accuracy) => {
  const gap = parseFloat(target) - parseFloat(accuracy);

  if (gap <= 0.05) {
    return "A";
  }
  if (gap > 0.05 && gap <= 0.15) {
    return "B";
  }
  if (gap > 0.15 && gap <= 0.25) {
    return "C";
  }
  if (gap > 0.25 && gap <= 0.35) {
    return "D";
  }
  return "E";
};

export { capitaliseFirstLetter, parseObjIdString, formatAccuracy, getGrade };
