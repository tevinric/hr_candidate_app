import streamlit as st
from utils import format_datetime_gmt_plus_2, format_current_time_gmt_plus_2


def dashboard_tab():
    st.markdown('<div class="section-header"><h2>📊 Dashboard</h2></div>', unsafe_allow_html=True)
    
    # Show current time in GMT+2
    current_time = format_current_time_gmt_plus_2()
    st.markdown(f"**Current Time:** {current_time}")
    
    # Get statistics
    stats = st.session_state.db_manager.get_dashboard_stats()
    sync_status = st.session_state.db_manager.get_sync_status()
    
    # Professional metrics display
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Candidates", stats.get('total_candidates', 0))
    
    with col2:
        st.metric("Industries", stats.get('unique_industries', 0))
    
    with col3:
        st.metric("Avg Experience", f"{stats.get('avg_experience', 0):.1f} years")
    
    with col4:
        backup_status = "✅ Active" if st.session_state.db_manager.last_backup_time else "❌ Never"
        st.metric("Backup Status", backup_status)
    
    with col5:
        db_size = f"{stats.get('database_size_mb', 0):.1f} MB"
        st.metric("DB Size", db_size)
    
    # Sync Status Section
    st.markdown("---")
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("🔄 Database Sync Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if sync_status['last_sync_time']:
            # Format last sync time in GMT+2
            last_sync_formatted = format_datetime_gmt_plus_2(sync_status['last_sync_time'].isoformat())
            st.success(f"✅ Last sync: {last_sync_formatted}")
        else:
            st.warning("⚠️ No sync performed yet")
        
        if sync_status['is_syncing']:
            st.info("🔄 Sync in progress...")
        
        # Show local database info
        if sync_status['local_db_exists']:
            st.info(f"📁 Local DB size: {sync_status['local_db_size'] / (1024*1024):.1f} MB")
        else:
            st.warning("⚠️ Local database not found")
    
    with col2:
        sync_col1, sync_col2 = st.columns(2)
        
        with sync_col1:
            if st.button("📤 Sync to Cloud", type="primary", help="Upload local changes to blob storage"):
                with st.spinner("Syncing to cloud..."):
                    result = st.session_state.db_manager.sync_database()
                    if result:
                        st.success("✅ Sync successful!")
                        st.rerun()
                    else:
                        st.error("❌ Sync failed!")
        
        with sync_col2:
            if st.button("📥 Refresh from Cloud", help="Download latest from blob storage"):
                with st.spinner("Refreshing from cloud..."):
                    result = st.session_state.db_manager.refresh_database()
                    if result:
                        st.success("✅ Refresh successful!")
                        st.rerun()
                    else:
                        st.error("❌ Refresh failed!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Backup controls with professional styling
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("🔄 Database Backup")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Create Backup Now", type="primary"):
            with st.spinner("Creating backup..."):
                result = st.session_state.db_manager.backup_to_blob()
                if result:
                    backup_time = format_current_time_gmt_plus_2()
                    st.markdown(f'<div class="success-message">✅ Backup created successfully at {backup_time}!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">❌ Backup failed!</div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("📥 Restore from Latest Backup"):
            with st.spinner("Restoring from backup..."):
                result = st.session_state.db_manager.restore_from_backup()
                if result:
                    restore_time = format_current_time_gmt_plus_2()
                    st.markdown(f'<div class="success-message">✅ Database restored successfully at {restore_time}!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown('<div class="error-message">❌ Restore failed!</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)