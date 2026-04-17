const getItemListingID = (item_index, item_component_index) => {
  const itemTypeRef = "text";
  return ["artwork", String(item_index), itemTypeRef, String(item_component_index)].join("-");
};

const mergeArrays = (arr1 = [], arr2 = []) => {
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
