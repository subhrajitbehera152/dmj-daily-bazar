import html
import streamlit as st
from config import CATEGORY_GROUPS
from services.authentication import is_admin_logged_in
from services.inventory_service import get_item_by_id, get_all_shops, update_item
from components.navigation import navigate_to, render_brand_header


def render_admin_edit_item_page() -> None:
    if not is_admin_logged_in():
        navigate_to("admin_login")
        return

    item_id = st.session_state.get("edit_item_id")
    if not item_id:
        navigate_to("admin_dashboard")
        return

    item = get_item_by_id(int(item_id))
    if not item:
        st.error("Item not found.")
        if st.button("← Back to Dashboard"):
            navigate_to("admin_dashboard")
        return

    shops = get_all_shops()
    render_brand_header(f"Edit Product · {item[1]}")

    existing_cat = (item[2] or "").strip()
    detected_main = "Existing / Other Category"
    for main_k, subs in CATEGORY_GROUPS.items():
        if any(s[0].lower() == existing_cat.lower() for s in subs):
            detected_main = main_k
            break

    main_options = list(CATEGORY_GROUPS.keys()) + ["Existing / Other Category"]
    default_main_idx = main_options.index(detected_main) if detected_main in main_options else len(main_options) - 1

    col_form, col_preview = st.columns([2.2, 1], gap="large")

    with col_preview:
        with st.container(border=True):
            st.markdown("**Current Image Preview**")
            img_url = item[4] or "https://via.placeholder.com/300x200.png?text=No+Image"
            st.markdown(
                f'<div class="dmj-prod-img-wrap" style="height:200px;">'
                f'<img class="dmj-prod-img" src="{html.escape(img_url)}" '
                'onerror="this.onerror=null;this.src=\'https://via.placeholder.com/300x200.png?text=No+Image\';">'
                f"</div>",
                unsafe_allow_html=True,
            )

    with col_form:
        with st.container(border=True):
            selected_main = st.selectbox("Main Category", options=main_options, index=default_main_idx)

            with st.form("edit_item_form"):
                name = st.text_input("Product Name", value=item[1])

                if selected_main == "Existing / Other Category":
                    category = st.text_input("Existing Category", value=existing_cat)
                else:
                    sub_list = [s[0] for s in CATEGORY_GROUPS[selected_main]]
                    sub_idx = next((i for i, s in enumerate(sub_list) if s.lower() == existing_cat.lower()), 0)
                    category = st.selectbox("Sub-Category", options=sub_list, index=sub_idx)

                price = st.number_input("Price (₹)", min_value=0.0, value=float(item[3]), step=0.5, format="%.2f")
                photo = st.text_input("Image URL", value=item[4] or "")

                shop_labels = [s[1] for s in shops]
                shop_ids = [s[0] for s in shops]
                shop_idx = shop_ids.index(item[5]) if item[5] in shop_ids else 0
                selected_shop_idx = st.selectbox(
                    "Shop",
                    options=range(len(shops)),
                    index=shop_idx,
                    format_func=lambda i: shop_labels[i],
                )

                is_oos = st.toggle("Mark as Out of Stock", value=bool(item[6]))

                c1, c2 = st.columns(2)
                save_clicked = c1.form_submit_button("✅ Save Changes", type="primary", use_container_width=True)
                cancel_clicked = c2.form_submit_button("← Cancel", use_container_width=True)

                if cancel_clicked:
                    navigate_to("admin_dashboard")

                if save_clicked:
                    ok, err = update_item(
                        item_id=int(item_id),
                        name=name,
                        category=category,
                        price=price,
                        photo=photo,
                        shop_id=shop_ids[selected_shop_idx],
                        is_out_of_stock=is_oos,
                    )
                    if ok:
                        st.success("Product updated.")
                        navigate_to("admin_dashboard")
                    else:
                        st.error(err)
