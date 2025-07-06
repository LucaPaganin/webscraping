def filter_items_by_parent(items, parent_name=None, parent_type=None, parent_id=None):
    """
    Filter items from API response based on parent criteria.
    
    Args:
        items: List of items from API response
        parent_name: Filter by parent with this name (case-insensitive)
        parent_type: Filter by parent with this type
        parent_id: Filter by parent with this ID
        
    Returns:
        List of filtered items
    """
    if not items:
        return []
        
    filtered_items = []
    
    for item in items:
        # Skip items without parents
        if "parents" not in item or not item["parents"]:
            continue
            
        # Check if any parent matches all provided criteria
        for parent in item["parents"]:
            matches = True
            
            if parent_name is not None:
                if "label" not in parent or not parent["label"] or parent["label"].lower() != parent_name.lower():
                    matches = False
                    
            if parent_type is not None:
                if "type" not in parent or parent["type"] != parent_type:
                    matches = False
                    
            if parent_id is not None:
                if "id" not in parent or parent["id"] != parent_id:
                    matches = False
                    
            if matches:
                filtered_items.append(item)
                break  # Found matching parent, no need to check others
    
    return filtered_items
