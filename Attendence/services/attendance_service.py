# Attendence/services/attendance_service.py
import streamlit as st
from Attendence.core.clients import create_supabase_client
from Attendence.core.logger import get_logger
from Attendence.core.utils import current_ist_date

logger = get_logger(__name__)

@st.cache_data(ttl=30)
def fetch_attendance_records(class_name, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        # Defaults to ordering by date desc
        response = supabase.table("attendance").select("*").eq("class_name", class_name).order("date", desc=True).execute()
        return response.data if response.data else []
    except Exception:
        logger.exception(f"Failed to fetch attendance for {class_name}")
        raise

def fetch_roll_map(class_name, roll_number, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("roll_map").select("name").eq("class_name", class_name).eq("roll_number", roll_number).execute()
        return response.data[0]["name"] if response.data else None
    except Exception:
        logger.exception("Failed to fetch roll map")
        raise

def lock_roll_map(class_name, roll_number, name, supabase=None):
    if not supabase:
        supabase = create_supabase_client()
    try:
        supabase.table("roll_map").insert({
            "class_name": class_name,
            "roll_number": roll_number,
            "name": name
        }).execute()
    except Exception:
        logger.exception("Failed to lock roll map")
        raise

def check_existing_attendance(class_name, roll_number, date=None, supabase=None):
    if not date:
        date = current_ist_date()
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("attendance").select("*").eq("class_name", class_name).eq("roll_number", roll_number).eq("date", date).execute()
        return bool(response.data)
    except Exception:
        logger.exception("Failed to check existing attendance")
        raise

def get_daily_count(class_name, date=None, supabase=None):
    if not date:
        date = current_ist_date()
    if not supabase:
        supabase = create_supabase_client()
    try:
        response = supabase.table("attendance").select("*", count="exact").eq("class_name", class_name).eq("date", date).execute()
        return response.count or 0
    except Exception:
        logger.exception("Failed to get daily count")
        raise

def submit_attendance(class_name, roll_number, name, date=None, supabase=None):
    if not date:
        date = current_ist_date()
    if not supabase:
        supabase = create_supabase_client()
    try:
        supabase.table("attendance").insert({
            "class_name": class_name,
            "roll_number": roll_number,
            "name": name,
            "date": date
        }).execute()
        fetch_attendance_records.clear()
        return True
    except Exception:
        logger.exception("Failed to submit attendance")
        raise
