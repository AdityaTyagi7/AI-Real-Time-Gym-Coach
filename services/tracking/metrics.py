import streamlit as st
import time
from services.config.workout_config import METRICS_FIELDS
from services.persistence.exercise_repository import add_exercise


def save_pending_workout_progress():
    exercise = st.session_state.get("exercise_type")
    user_id = st.session_state.get("user_id")
    reps = st.session_state.get("reps", 0) or 0
    reps_per_set = st.session_state.get("reps_per_set", 0) or 0

    if not exercise or not isinstance(user_id, int) or reps <= 0 or reps_per_set <= 0:
        return

    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0)
    sets_completed = reps // reps_per_set
    last_saved_reps = st.session_state.get(
        "last_saved_reps",
        last_saved_sets * reps_per_set,
    )
    pending_reps = reps - last_saved_reps
    pending_sets = max(0, sets_completed - last_saved_sets)

    if pending_reps <= 0 and pending_sets <= 0:
        return

    now_ts = time.time()
    started_at = st.session_state.get("set_cycle_started_at", now_ts)
    add_exercise(
        user_id,
        exercise,
        max(0, pending_reps),
        pending_sets,
        now_ts - started_at,
    )
    st.session_state.last_saved_reps = reps
    st.session_state.last_saved_sets_completed = max(last_saved_sets, sets_completed)
    st.session_state.set_cycle_started_at = now_ts


def sync_metrics_update(context):
    if not context or not hasattr(context, "state") or not context.state.playing:
        return
    
    processor = getattr(context, "video_processor", None)

    if not processor:
        return 
    
    exercise = st.session_state.get("exercise_type")

    if not exercise:
        return
    
    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return
    
    reps = latest_metrics.get("reps", 0)

    if reps is None:
        reps = 0
        
    st.session_state.reps = reps

    fields = METRICS_FIELDS.get(exercise)

    if not fields:
        return 

    for key, default in fields.items():
        st.session_state[key] = latest_metrics.get(key, default)

    reps_per_set = st.session_state.get("reps_per_set", 0)
    target_sets = st.session_state.get("target_sets", 0)

    if reps is not None and reps_per_set > 0 and target_sets > 0:
        sets_completed = reps // reps_per_set
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_sets 
    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0)

    if target_sets > 0 and reps_per_set > 0 and sets_completed > last_saved_sets:
        newly_completed = sets_completed - last_saved_sets
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at", now_ts)
        time_taken = now_ts - started_at
        user_id = st.session_state.get("user_id", 0)

        add_exercise(user_id, exercise, newly_completed * reps_per_set, newly_completed, time_taken)
        st.session_state.last_saved_reps = sets_completed * reps_per_set

        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="set_completed",
                exercise=exercise,
                metrics=latest_metrics,
            )

            if result:
                st.session_state.audio_to_play, st.session_state.coach_feedback = result

        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed

    pose_detected = latest_metrics.get("pose_detected", True)
    was_pose_detected = st.session_state.get("last_pose_detected", True)

    if pose_detected:
        st.session_state.last_pose_detected = True
    else:
        if was_pose_detected and st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="no_pose_detected",
                exercise=exercise,
                metrics={"issue": "No pose detected! Please step into the camera frame."},
            )

            if result:
                st.session_state.audio_to_play, st.session_state.coach_feedback = result

        st.session_state.last_pose_detected = False