const prepareCsvData = (dataset_artworks, results, labels, labelset_type, dataset_type, setCsvData) => {
  const dataset_with_preds = dataset_artworks.map((item) => {
    const mappedItem = {
      ...item,
      order: item.position,
    };

    if (labels.length > 0) {
      const label = labels.find((e) => e.item_id === mappedItem._id);
      if (typeof label !== "undefined") {
        if (labelset_type === "binary") {
          mappedItem.label = label.value === 0 ? "negative" : "positive";
        } else {
          mappedItem.label = label.value;
        }
        mappedItem.rationale = label.rationale;
      }
    }

    const item_result = results.find((result) => Object.keys(result).includes(mappedItem._id));
    mappedItem.predicted = typeof item_result !== "undefined" ? item_result[mappedItem._id] : "";

    let allowed;
    if (dataset_type === "image") {
      mappedItem.id = mappedItem.content[0].content_value.text.replace(/,/g, "");
      allowed = ["order", "id", "predicted"];
    } else if (dataset_type === "text") {
      mappedItem.text = mappedItem.content[0].content_value.text.replace(/,/g, "");
      allowed = ["order", "text", "predicted"];
    } else if (dataset_type === "textimage") {
      mappedItem.id = mappedItem.content[0].content_value.text.replace(/,/g, "");
      mappedItem.text = mappedItem.content[1].content_value.text.replace(/,/g, "");
      allowed = ["order", "id", "text", "predicted"];
    }

    if (labels.length > 0) {
      allowed.push("label", "rationale");
    }
    if (dataset_artworks.some((e) => e.object_id != null)) {
      allowed.push("object_id");
    }

    return Object.fromEntries(Object.entries(mappedItem).filter(([key]) => allowed.includes(key)));
  });

  const headers = [{ label: "order", key: "order" }];

  if (dataset_artworks.some((e) => e.object_id != null)) {
    headers.push({ label: "object_id", key: "object_id" });
  }

  if (dataset_type === "image") {
    headers.push({ label: "filename", key: "id" }, { label: "predicted", key: "predicted" });
  } else if (dataset_type === "text") {
    headers.push({ label: "text", key: "text" }, { label: "predicted", key: "predicted" });
  } else if (dataset_type === "textimage") {
    headers.push(
      { label: "filename", key: "id" },
      { label: "text", key: "text" },
      { label: "predicted", key: "predicted" },
    );
  }

  if (labels.length > 0) {
    headers.push({ label: "label", key: "label" });
  }
  if (labels.some((e) => e.rationale != "")) {
    headers.push({ label: "rationale", key: "rationale" });
  }

  setCsvData([dataset_with_preds, headers]);
};

export { prepareCsvData };
