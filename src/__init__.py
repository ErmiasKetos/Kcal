# src/__init__.py

from .registration_page import registration_page
from .calibration_page import calibration_page
from .inventory_review import inventory_review_page
from .dashboard import render_dashboard
from .inventory_manager import InventoryManager

# Initialize inventory manager at module level if needed
def init_app():
    if 'inventory_manager' not in st.session_state:
        st.session_state.inventory_manager = InventoryManager()
        st.session_state.inventory_manager.initialize_inventory()

__all__ = [
    'registration_page',
    'calibration_page',
    'inventory_review_page',
    'render_dashboard',
    'InventoryManager',
    'init_app'
]
