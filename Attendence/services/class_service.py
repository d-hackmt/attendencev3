# Attendence/services/class_service.py
import streamlit as st
from Attendence.core.clients import create_supabase_client
from Attendence.core.logger import get_logger

logger = get_logger(__name__)

@st.cache_data(ttl=60)
def get_all_classes(supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("classroom_settings").select("*").execute()
        return response.data if response.data else []
    except Exception:
        logger.exception("Failed to fetch classes")
        raise

@st.cache_data(ttl=60)
def get_open_classes(supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("classroom_settings").select("class_name").eq("is_open", True).execute()
        return [entry["class_name"] for entry in response.data] if response.data else []
    except Exception:
        logger.exception("Failed to fetch open classes")
        raise

def create_class(class_name, code="1234", daily_limit=10, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        # Check if exists
        exists = supabase.table("classroom_settings").select("*").eq("class_name", class_name).execute().data
        if exists:
            return False, "Class already exists."
        
        supabase.table("classroom_settings").insert({
            "class_name": class_name,
            "code": code,
            "daily_limit": daily_limit,
            "is_open": False
        }).execute()
        get_all_classes.clear()
        return True, f"Class '{class_name}' created."
    except Exception as e:
        logger.exception(f"Failed to create class {class_name}")
        return False, str(e)

def delete_class(class_name, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        supabase.table("attendance").delete().eq("class_name", class_name).execute()
        supabase.table("roll_map").delete().eq("class_name", class_name).execute()
        supabase.table("classroom_settings").delete().eq("class_name", class_name).execute()
        get_all_classes.clear()
        get_open_classes.clear()
        return True
    except Exception:
        logger.exception(f"Failed to delete class {class_name}")
        raise

def update_class_status(class_name, is_open, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        supabase.table("classroom_settings").update({"is_open": is_open}).eq("class_name", class_name).execute()
        get_all_classes.clear()
        get_open_classes.clear()
    except Exception:
        logger.exception(f"Failed to update status for {class_name}")
        raise

def update_class_settings(class_name, code, daily_limit, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        supabase.table("classroom_settings").update({"code": code, "daily_limit": daily_limit}).eq("class_name", class_name).execute()
        get_all_classes.clear()
    except Exception:
        logger.exception(f"Failed to update settings for {class_name}")
        raise
