# Phase 2A: User Baseline Endpoints
# These endpoints will be added to src/api/main.py after line 445

# ============================================================================
# ENDPOINT 1: GET ALL USERS WITH BASELINES
# ============================================================================
@app.get("/users", response_model=List[UserSummary], summary="Get All Users with Baselines")
def get_all_users():
    """
    Returns a list of all users with their baseline information.
    
    Useful for populating user selection dropdowns in frontend.
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.profile_manager is None:
        raise HTTPException(status_code=503, detail="User profiles not initialized")
    
    try:
        users = data_store.profile_manager.get_all_users()
        return [UserSummary(**user) for user in users]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT 2: GET DETAILED BASELINE FOR SPECIFIC USER
# ============================================================================
@app.get("/users/{user_id}/baseline", response_model=UserBaseline, summary="Get User Baseline Details")
def get_user_baseline(user_id: str):
    """
    Returns detailed baseline information for a specific user.
    
    Includes:
    - Baseline metrics (avg file access, upload sizes, typical hours, etc.)
    - Behavioral fingerprint (USB usage, sensitive file patterns, etc.)
    - Baseline risk level
    - Data quality/confidence metrics
    
    - **user_id**: User ID to get baseline for
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.profile_manager is None:
        raise HTTPException(status_code=503, detail="User profiles not initialized")
    
    try:
        profile = data_store.profile_manager.get_profile(user_id)
        
        if profile is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return UserBaseline(**profile.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting baseline for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT 3: GET DIVERGENCE ANALYSIS FOR AN EVENT
# ============================================================================
@app.get("/users/{user_id}/divergence/{event_id}", response_model=DivergenceAnalysis,
         summary="Get Divergence Analysis for Event")
def get_divergence_analysis(user_id: str, event_id: str):
    """
    Calculates how much an event diverges from the user's baseline behavior.
    
    Returns:
    - Divergence score (0.0 to 2.0+)
    - Divergence level (Low/Medium/High)
    - Detailed explanations of what diverged
    - Comparison with user's baseline
    
    - **user_id**: User ID
    - **event_id**: Event ID to analyze
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.profile_manager is None:
        raise HTTPException(status_code=503, detail="User profiles not initialized")
    
    try:
        # Get user profile
        profile = data_store.profile_manager.get_profile(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get event
        event_row = data_store.df[data_store.df['event_id'] == event_id]
        if event_row.empty:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        
        # Calculate divergence
        event = event_row.iloc[0]
        divergence = profile.calculate_divergence(event)
        
        return DivergenceAnalysis(**divergence)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating divergence: {e}")
        raise HTTPException(status_code=500, detail=str(e))
