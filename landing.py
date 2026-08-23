"""GISGPT Landing Page — เสิร์ฟหน้าแรกจาก frontend/dist (Vite + React)

ทุกอย่างของหน้า Landing แยกอยู่ในโฟลเดอร์ frontend/ ทั้งหมด
ถ้ายังไม่ได้ build (ไม่มี dist/) จะ fallback ไปหน้า chat เดิมกันเว็บพัง
"""
import os

from flask import Blueprint, render_template, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE_DIR, "frontend", "dist")

landing_bp = Blueprint("landing", __name__)


@landing_bp.route("/")
def index():
    if os.path.exists(os.path.join(DIST, "index.html")):
        return send_from_directory(DIST, "index.html")
    return render_template("index.html")


@landing_bp.route("/assets/<path:name>")
def assets(name):
    return send_from_directory(os.path.join(DIST, "assets"), name)
