const getItemListingID = (item_index: string | number, item_component_index: string | number): string => {
  const itemTypeRef = "text";
  return ["artwork", String(item_index), itemTypeRef, String(item_component_index)].join("-");
};

type MergeableRecord = Record<string, unknown> & {
  id?: string | number;
  address?: unknown;
};

const mergeArrays = (arr1: MergeableRecord[] = [], arr2: MergeableRecord[] = []): MergeableRecord[] => {
  return arr1.map((obj) => {
    const index = arr2.findIndex((el) => el.id == obj.id);
    const { address } = index !== -1 ? arr2[index] : {};
    return {
      ...obj,
      address,
    };
  });
};

export { getItemListingID, mergeArrays };
