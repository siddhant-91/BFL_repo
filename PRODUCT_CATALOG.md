# Adding products to BFL

Product entry is managed from the owner dashboard. Start at `/manage/`, sign in, and choose **Add a product**. The editor separates the product story and main photo, product details and size system, size measurements, stock variants, and optional gallery photos.

## Before opening the editor

For each style, prepare:

- One clear front photo for the main listing image. Use a consistent portrait crop and neutral background where possible.
- Optional photos showing the back, fabric detail, fit, or other colors.
- Product name, category, short description, fabric, fit, care instructions, printed MRP, and BFL price.
- Each sellable color/size combination, its unique SKU, and the physical quantity available.
- Measurements for each available size, measured on the garment in centimetres.

Keep photo files named with the style or SKU so they are easy to find later, for example `BFL-TEE-001-black-front.jpg` and `BFL-TEE-001-black-detail.jpg`. Avoid uploading photos that contain customer details or unrelated images.

## Add one product

1. **Product:** Enter the name and choose its category. Write 2–4 short sentences about fabric, feel, fit, and useful details. The description is customer-facing. The URL slug can be left to the editor's automatic suggestion.
2. **Photos:** Upload the front photo under the main product photo. Add a concise image description for accessibility, such as “Black cotton crew-neck T-shirt, front view.” Add extra angles in the optional gallery photos below the product fields.
3. **Details and sizing:** Choose one size system for this product: alpha sizes, waist inches, numeric sizes, one size, or custom. Use consistent labels for style, fit, and color across the catalog so shoppers can filter reliably.
4. **Price and promotion:** Enter BFL's selling price and the printed MRP. The MRP must be higher than the selling price; BFL calculates the discount percentage automatically.
5. **Size guide:** Add one measurement row for every size that will be sold. Use the illustrated guide shown on the product page to measure the garment flat, in centimetres. T-shirts and other upper garments use chest, shoulder, garment length, and sleeve length. Jeans use waist, hip, rise, and inseam. Accessories use foot length where relevant.
6. **Stock:** Add one variant row for every color and size combination. Give every row a unique SKU and enter the actual quantity on hand. For example, a black tee in M and L is two rows. Set a variant's stock to zero or switch it off when that size/color cannot be sold.
7. **Homepage feature:** Turn on the homepage feature option for items to include in the rotating front-page display, and use a lower feature order to show an item earlier.
8. **Publish:** Keep the product as a draft while details are incomplete. A published product needs a main photo, a price below MRP, at least one size/color stock variant, and a measurement row for each sellable size. Save, then open its product page and test size selection and add-to-cart.

## Example description

> Soft cotton jersey with a relaxed fit and a clean ribbed crew neck. Designed for everyday wear and easy layering. Wash with similar colors.

Use your own accurate product details; do not claim a fabric, fit, or feature that the item does not have.

## Staging before public launch

Use the staging website for sample listings first. Upload a sample hero photo and gallery image, create at least two sizes and one color, enter measurements and stock, and check the listing on mobile and desktop. Place a test cash-on-delivery order and verify that the selected size appears correctly and inventory decreases. Once the flow is right, add production listings to the production site. Staging and production use separate databases and photo buckets, so products entered in staging do not copy over automatically.

The MVP is designed for entering products one at a time through the dashboard. If BFL starts loading dozens or hundreds of products in a batch, add a spreadsheet import/export workflow later, with image files referenced by filename and a preview/validation step before import.
