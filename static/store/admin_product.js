(() => {
  const options = {
    alpha: ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"],
    waist: ["26", "28", "30", "32", "34", "36", "38", "40", "42", "44"],
    numeric: ["36", "38", "40", "42", "44", "46", "48", "50", "52"],
    one_size: ["One Size"],
  };
  const schemeField = document.getElementById("id_size_system");
  if (!schemeField) return;

  const replaceWithSelect = (field, values) => {
    const current = field.value;
    const select = document.createElement("select");
    select.name = field.name;
    select.id = field.id;
    select.className = field.className;
    select.required = true;
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "Choose a size";
    select.appendChild(blank);
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
    select.value = values.includes(current) ? current : "";
    field.replaceWith(select);
  };

  const replaceWithText = (field) => {
    if (field.tagName === "INPUT") return;
    const input = document.createElement("input");
    input.type = "text";
    input.name = field.name;
    input.id = field.id;
    input.className = field.className;
    input.value = field.value;
    input.required = true;
    field.replaceWith(input);
  };

  const applyScheme = () => {
    const scheme = schemeField.value;
    const sizes = options[scheme];
    document.querySelectorAll('[name$="-size"]').forEach((field) => {
      if (!sizes) replaceWithText(field);
      else if (field.tagName !== "SELECT") replaceWithSelect(field, sizes);
      else {
        const current = field.value;
        field.replaceChildren(new Option("Choose a size", ""));
        sizes.forEach((size) => field.add(new Option(size, size)));
        field.value = sizes.includes(current) ? current : "";
      }
    });
  };

  schemeField.addEventListener("change", applyScheme);
  document.addEventListener("click", (event) => {
    if (event.target.closest(".add-row")) window.setTimeout(applyScheme, 0);
  });
  applyScheme();
})();
