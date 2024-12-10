import pandas as pd

import plotly.graph_objs as go


def get_dataframe(twix_map_obj, additional_cols=[], time_ref=None):
    """Build a dataframe from a twix_map_obj

    Args:
        twix_map_obj (twix_map_obj): input twix map obj (like twix[-1])
        additional_cols (list, optional): additional columns to add. Defaults to [].
        time_ref (_type_, optional): Reference time used while converting in seconds. Defaults to None.

    Returns:
        pd.DataFrame: output dataframe of the twix_map_obj
    """
    df = pd.DataFrame({
        "Time": twix_map_obj.timestamp,
        "Lin": twix_map_obj.Lin.astype(int), 
        "Sli": twix_map_obj.Sli.astype(int), 
        "Par": twix_map_obj.Par.astype(int), 
        "Seg": twix_map_obj.Seg.astype(int),
    })
    # add additional columns
    if not isinstance(additional_cols, list):
        additional_cols = [additional_cols]
    for col in additional_cols:
        df[col] = twix_map_obj.__getattribute__(col).astype(int) 
    # set default time reference
    if time_ref is None:
        time_ref = df.Time[0]
    # display time in seconds from the start
    df.Time -= time_ref
    df.Time *= 2.5e-3
    df['Time'] = df['Time'].apply(lambda x: round(x, 5)) # round time
    # keep only time after time ref
    mask = df.Time>0
    return df[mask]


def table(df, rename=True, title=None, height=500):
    """Show a dataframe in a nice format using plotly

    Args:
        df (pd.DataFrame): input dataframe
        rename (bool, optional): Whether to rename twix columns. Defaults to True.
        height (float): height of the figure

    Returns:
        plotly.graph_objs.figure: output figure
    """
    if rename:
        columns={
            'Time': 'Time (s)',
            'delta': 'Delta time (ms)',
            'Lin': 'Line',
            'Sli': 'Slice',
            'Par': 'Partition',
        }
        for c, new_c in columns.items():
            if c in df.columns:
                df.rename(
                    columns={c:new_c},
                    inplace=True
                )
    fig = go.Figure(data=[go.Table(
    header=dict(values=list(df.columns),
                align='left'),
    cells=dict(values=[df[i] for i in df.columns],           
                align='left'))
    ])
    if title:
        fig.update_layout(title=title, title_x=0.5, height=height)
    return fig


def get_concat_dataframe(list_twix: list, refscan=True, 
                         rtfeedback=True, **kwargs):
    """Get concat dataframe from a list of mapvbvd.mapVBVD.myAttrDict

    Args:
        list_twix (list): input list of mapVBVD.myAttrDict
        refscan (bool, optional): Whether to keep refscan. Defaults to True.
        rtfeedback (bool, optional): Whether to keep rtfeedback. Defaults to True.

    Returns:
        pd.DataFrame: output total dataframe for all keys (image, refscan, rtfeedback)
    """
    keys_available = list_twix[-1].keys()
    keys = ['image']
    if refscan and 'refscan' in keys_available:
        keys.append('refscan')
    if rtfeedback and 'rtfeedback' in keys_available:
        keys.append('rtfeedback')
    time_ref = list_twix[-1]['image'].timestamp[0]
    twix_map_objs = [list_twix[-1][k] for k in keys]
    df_concat = pd.concat(
        {
            k: get_dataframe(twix_map_obj, time_ref=time_ref, **kwargs)
            for k, twix_map_obj in zip(keys, twix_map_objs)
        },
        names=['tag']
    )
    df_concat = df_concat.reset_index(level='tag')
    new_columns = [*df_concat.columns[1:], df_concat.columns[0]]
    df_concat=df_concat.reindex(columns=new_columns)
    df_concat.drop_duplicates(inplace=True, subset=['Time', 'Sli', 'Seg', 'Par'])
    df_concat.sort_values(by='Time', inplace=True, ignore_index=True)
    return df_concat