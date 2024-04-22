"""Program to build cadence, gait plots and save them as .png files."""

import sys
from typing import Final

import numpy as np

from graphical import LEG_LENGTH, ROTATE, SAMPLING, X_CENTER, read
from scipy.interpolate import make_interp_spline


def generate_cadence_plot(in_filename: str, out_filename: str) -> None:
    """
    Generate cadence plot
    Parameters
    ----------
    userId : str
        User ID
    runId : str
        Run ID
    cadence : list[int]
        Cadence
    time : list[str]
        Time

    Returns
    -------
    str
        Cadence plot link
    """
    # import plotly
    import plotly.graph_objects as go

    # first create the figure
    with open(in_filename, "r") as f:
        data: Final[list[str]] = f.read().split("\n")
        ls, lt, rs, rt = read(data)

        cadence = []
        spm = []
        for it in range(len(lt) - 2):
            transfer_x = LEG_LENGTH * np.cos(lt[it][2] + ROTATE)
            transfer_x2 = LEG_LENGTH * np.cos(lt[it + 1][2] + ROTATE)
            if (X_CENTER + transfer_x) > X_CENTER and (
                X_CENTER + transfer_x2
            ) < X_CENTER:
                cadence.append(it / SAMPLING)
                if len(cadence) > 1:
                    multiplier = 1 / ((cadence[-1] - cadence[0]) / 60)
                    spm.append(round(len(cadence) * multiplier, 2))
        # plot spm using plotly
        figure = go.Figure(
            layout_title_text="Cadence Over Your Run",
            data=[
                go.Scatter(
                    x=cadence,
                    y=spm,
                    mode="lines+markers",
                    line_shape="spline",
                )
            ],
        )
        figure.update_xaxes(title_text="Time (s)")
        figure.update_yaxes(title_text="Strides per minute")
        figure.write_image(out_filename)


def generate_average_stride_plots(in_filename: str, out_filename: str) -> None:
    """
    Generate average stride plots
    Parameters
    ----------
    userId : str
        User ID
    runId : str
        Run ID
    filename : str
        File name

    Returns
    -------
    str
        Average stride plot link
    """
    # import plotly
    import plotly.graph_objects as go

    # first create the figure
    print(in_filename, out_filename)
    with open(in_filename, "r") as f:
        data: Final[list[str]] = f.read().split("\n")
        ls, lt, rs, rt = read(data)

        stride_length_lists = []
        cadence = []

        previous_spm_index = 0
        spm = []
        spm_index = []
        spm_length = []
        for it in range(len(lt) - 2):
            transfer_x = LEG_LENGTH * np.cos(lt[it][2] + ROTATE)
            transfer_x2 = LEG_LENGTH * np.cos(lt[it + 1][2] + ROTATE)
            if (X_CENTER + transfer_x) > X_CENTER and (
                X_CENTER + transfer_x2
            ) < X_CENTER:
                cadence.append(it / SAMPLING)
                if len(cadence) > 1:
                    multiplier = 1 / ((cadence[-1] - cadence[0]) / 60)
                    spm_value = round(len(cadence) * multiplier, 2)
                    if spm_value > 30:  # if cadence is greater than 30 strides a minute
                        # add all the strides from previous_spm_index to now to list
                        spm.append(spm_value)
                        spm_index.append(it)
                        spm_length.append(it - previous_spm_index)

                    previous_spm_index = it
                    if len(cadence) > 60:
                        cadence = []

        # get median spm
        median_spm = np.percentile(spm, 0.5, interpolation="nearest")
        # get index for median_spm
        median_spm_index = spm.index(median_spm)
        print(
            f"Median spm: {median_spm}, index: {spm_index[median_spm_index]}, length: {spm_length[median_spm_index]}"
        )
        # plot spm using plotly
        x = [i for i in range(spm_length[median_spm_index] + 1)]
        xnew = np.linspace(0, spm_length[median_spm_index], 100)
        leg_names = ["Left", "Right"]
        y_interpolated = {}
        for i, leg in enumerate(leg_names):
            if leg == "Left":
                y_just_second_index = np.subtract(
                    [
                        i[1]
                        for i in lt[
                            spm_index[median_spm_index]
                            - spm_length[median_spm_index]
                            - 1 : spm_index[median_spm_index]
                        ]
                    ],
                    [
                        i[1]
                        for i in ls[
                            spm_index[median_spm_index]
                            - spm_length[median_spm_index]
                            - 1 : spm_index[median_spm_index]
                        ]
                    ],
                )
            else:
                y_just_second_index = np.subtract(
                    [
                        i[1]
                        for i in rt[
                            spm_index[median_spm_index]
                            - spm_length[median_spm_index]
                            - 1 : spm_index[median_spm_index]
                        ]
                    ],
                    [
                        i[1]
                        for i in rs[
                            spm_index[median_spm_index]
                            - spm_length[median_spm_index]
                            - 1 : spm_index[median_spm_index]
                        ]
                    ],
                )
            gfg = make_interp_spline(
                x,
                y_just_second_index,
                k=3,
            )

            y_interpolated[leg_names[i]] = gfg(xnew)

        figure = go.Figure(
            # make title
            layout_title_text="Median Stride",
            data=[
                go.Scatter(
                    x=[i / SAMPLING for i in xnew],
                    y=np.rad2deg(y_interpolated[leg_name]),
                    # name of the leg
                    name=leg_name,
                    mode="lines+markers",
                )
                for leg_name in leg_names
            ],
        )
        figure.update_xaxes(title_text="Time (s)")
        figure.update_yaxes(title_text="Degrees")
        figure.write_image(out_filename)


if __name__ == "__main__":
    data_file_name = sys.argv[1]
    print(data_file_name)
    generate_cadence_plot(data_file_name, "hi.png")
