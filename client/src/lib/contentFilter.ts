import type { ContentFilterError } from "@/types";

const getFilterErrorString = (errors: ContentFilterError[], allFiltered: boolean): string => {
  let error_string =
    allFiltered === false
      ? "Some predictions were not processed due to the following flagged themes: "
      : "All predictions were not processed due to the following flagged themes: ";

  let themes: string[] = [];
  errors.forEach((e) => {
    if (e.error?.code == "content_filter") {
      const content_filter_results = e.error?.inner_error?.content_filter_results ?? {};
      for (const [key, value] of Object.entries(content_filter_results)) {
        if (value.filtered) {
          const theme = key.replace("_", " ");
          themes.push(theme);
        }
      }
    }
  });

  themes = [...new Set(themes)];
  error_string += themes.join(", ");
  return error_string;
};

export { getFilterErrorString };
