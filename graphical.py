import os
import sys
from typing import Final
from datetime import datetime

import numpy as np
import pygame
from firebase_admin import storage

os.environ["IMAGEIO_FFMPEG_EXE"] = "/opt/homebrew/bin/ffmpeg"
shoes = "shoe.png"

import moviepy.video.io.ImageSequenceClip

# global variables
SCREEN_W = 600
SCREEN_H = 600
X_CENTER = SCREEN_W * 0.5
Y_CENTER = SCREEN_H * 0.5
LEG_LENGTH = 100
SAMPLING = 30

ROTATE = 1.5708

SNAPS = "/tmp/snaps"

data_file = "/tmp/data.run"


def read(file: list[str]) -> list[list[float]]:
    ls = []
    lt = []
    rs = []
    rt = []
    for line in file[1:]:  # skipping first line as first line is header
        if line == "":
            continue
        temp = line.split(",")
        ls.append([float(temp[0]), float(temp[1]), float(temp[2])])
        lt.append([float(temp[3]), float(temp[4]), float(temp[5])])
        rs.append([float(temp[6]), float(temp[7]), float(temp[8])])
        rt.append([float(temp[9]), float(temp[10]), float(temp[11])])

    return ls, lt, rs, rt


def get_knee_pos(LT, RT, iteration: float, leg: str, point: str):

    # if leg == "L":
    #     rad_thigh = np.pi / -180 * (LT[iteration][2])
    #     rad_shank = np.pi / -180 * (LS[iteration][2])
    # elif leg == "R":
    #     rad_thigh = np.pi / 180 * (RS[iteration][2])
    #     rad_shank = np.pi / 180 * (RS[iteration][2])

    # knee_x = LEG_LENGTH * np.sin(rad_thigh)
    # knee_y = LEG_LENGTH * np.cos(rad_thigh)

    # if point == "K":
    #     return [X_CENTER + knee_x, Y_CENTER + knee_y]
    # elif point == "S":
    #     shank_x = LEG_LENGTH * np.sin(rad_shank)
    #     shank_y = LEG_LENGTH * np.cos(rad_shank)
    #     return [X_CENTER + knee_x - shank_x, Y_CENTER + knee_y - shank_y]
    if leg == "L":
        return [
            Y_CENTER + LEG_LENGTH * np.cos(LT[iteration][1]),
            X_CENTER - LEG_LENGTH * np.sin(LT[iteration][1]),
        ]
    elif leg == "R":
        return [
            Y_CENTER + LEG_LENGTH * np.cos(RT[iteration][1]),
            X_CENTER - LEG_LENGTH * np.sin(RT[iteration][1]),
        ]


def get_shank_pos(LS, RS, it: float, knee_pos: list[float], leg: str):
    if leg == "L":
        return [
            knee_pos[0] - LEG_LENGTH * np.cos(LS[it][1]),
            knee_pos[1] - LEG_LENGTH * np.sin(LS[it][1]),
        ]
    elif leg == "R":
        return [
            knee_pos[0] - LEG_LENGTH * np.cos(RS[it][1]),
            knee_pos[1] - LEG_LENGTH * np.sin(RS[it][1]),
        ]


def create_video(image_folder: str, video_name: str) -> None:
    """
    Create video from images in folder
    Parameters
    ----------
    image_folder : str
        Folder
    video_name : str
        Video name
    """
    images = [
        f"{image_folder}/{img}"
        for img in os.listdir(image_folder)
        if img.endswith(".png")
    ]
    # sort by integer value
    images.sort(key=lambda x: int(x.split(".")[0].split("/")[-1]))
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(images, fps=SAMPLING)
    clip.write_videofile(video_name, fps=SAMPLING, threads=1, codec="libx264")
    print("video released!")

def check_pronate(rs: float, marker: float):
    vert_s = np.rad2deg(rs)
    diff = abs(abs(marker) - abs(vert_s))
    if diff >= 25:
        print(f"PRON: diff: {diff}")
        return (255, 0, 0)
    else: # green is fine
        return (0, 255, 0)

def check_supinate(rs: float, marker: float):
    vert_s = np.rad2deg(rs)
    diff = abs(abs(marker) - abs(vert_s))
    if diff >= 25:
        print(f"SUP: diff: {diff}")
        return (255, 0, 0)
    else: # green is fine
        return (0, 255, 0)


def calc_angle(LT, LS, RT, RS, iteration):
    l_thigh = np.rad2deg(LT[iteration][1])
    l_shank = np.rad2deg(LS[iteration][1])
    r_thigh = np.rad2deg(RT[iteration][1])
    r_shank = np.rad2deg(RS[iteration][1])

    l_angle = str(round(abs(l_thigh) + abs(l_shank), 2))
    r_angle = str(round(abs(r_thigh) + abs(r_shank), 2))

    return l_angle, r_angle

def create_video_from_file(
    *,
    LS: list[list[float]],
    LT: list[list[float]],
    RS: list[list[float]],
    RT: list[list[float]],
    video_link: str,
) -> str:
    """
    Create video from file
    Parameters
    ----------
    LS : list[list[float]]
        Left shank
    LT : list[list[float]]
        Left thigh
    RS : list[list[float]]
        Right shank
    RT : list[list[float]]
        Right thigh

    Returns
    -------
    str
        Video name
    """

    try:
        os.makedirs("/tmp/snaps")
    except OSError:
        pass

    try:
        os.makedirs("/tmp/movies")
    except OSError:
        pass

    pygame.init()
    # pygame.display.init()
    window = pygame.Surface((SCREEN_W, SCREEN_W))
    pygame.display.set_caption("2D Animation - Lateral Perspective")
    window.fill((0, 0, 0))

    # displaying text
    font_a = pygame.font.SysFont("Arial", 24)
    font_b = pygame.font.SysFont("Arial", 24)

    # initialize top of thigh position at center of screen
    l_thigh_pos = [X_CENTER, Y_CENTER]
    r_thigh_pos = [X_CENTER, Y_CENTER]

    # points of first values at start up
    marker_ang = round(LEG_LENGTH * np.cos(LS[0][1] + ROTATE), 2)
    marker_vert = round(np.rad2deg(RS[0][0]), 2)

    cadence = 0
    spm = 0
    iteration = 0
    # starting video
    file_num: int = 0

    while iteration < len(LS) - 1:
        file_num = file_num + 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break

        # displaying length of activity
        activity = str(round(iteration / SAMPLING, 2))
        activity_length = font_b.render(f"Length of activity: {activity}", True, (255, 255, 255), (0, 0, 0))
        window.blit(activity_length, (50, 50)) 

        # average cadence - when shank_l goes pos (forward) to neg (backwards)
        current_x = round(LEG_LENGTH * np.cos(LS[iteration][1] + ROTATE), 2)
        before_x = round(LEG_LENGTH * np.cos(LS[iteration + 1][1] + ROTATE), 2)
        # print(f"{marker_ang} | current: {current_x} vs before: {before_x}")
        if (current_x > marker_ang) and (before_x < marker_ang):
            cadence += 1
            spm = round(cadence / (iteration / SAMPLING / 60), 2)
        spm_text = font_b.render(f"Cadence: {spm} spm", True, (255, 255, 255), (0, 0, 0))
        window.blit(spm_text, (50, 80))

        # left and right knee pos
        l_knee_pos = get_knee_pos(LT, RT, iteration, "L", "K")
        r_knee_pos = get_knee_pos(LT, RT, iteration, "R", "K")

        # # left and right shank pos
        l_shank_pos = get_shank_pos(LS, RS, iteration, l_knee_pos, "L")
        r_shank_pos = get_shank_pos(LS, RS, iteration, r_knee_pos, "R")

        # displaying knee angles of respective legs
        left = "Left: "
        left_text = font_a.render(left, True, (0, 0, 255), (255, 0, 0))
        # displaying knee angles of respective legs
        l_angle, r_angle = calc_angle(LT, LS, RT, RS, iteration)

        left_text = font_b.render(f"Left: {l_angle}", True, (0, 0, 255), (255, 0 , 0))
        window.blit(left_text, (50, 110))

        right_text = font_b.render(f"Right: {r_angle}", True, (128, 0, 128), (0, 255, 0))
        window.blit(right_text, (50, 140))

        pygame.draw.line(
            window, (0, 255, 255), l_thigh_pos, l_knee_pos, width=3
        )  # blue = left thigh
        pygame.draw.line(
            window, (255, 0, 0), l_knee_pos, l_shank_pos, width=3
        )  # red = left shank
        print(r_thigh_pos, r_knee_pos, r_shank_pos)
        pygame.draw.line(
            window, (0, 255, 0), r_thigh_pos, r_knee_pos, width=3
        )  # green = right thigh
        pygame.draw.line(
            window, (128, 0, 128), r_knee_pos, r_shank_pos, width=3
        )  # yellow = right shank

        # pronation/supination and overstriding
        pronation_text = font_a.render(f"Pronation ", True, (255, 255, 255), (0, 0 , 0))
        pronation_rect = pronation_text.get_rect()
        pronation_rect.topright = (535, 50)
        window.blit(pronation_text, pronation_rect)

        supination_text = font_a.render(f"Supination ", True, (255, 255, 255), (0, 0, 0))
        supination_rect = supination_text.get_rect()
        supination_rect.topright = (535, 80)
        window.blit(supination_text, supination_rect)

        # supination is outwards aka marker>vert, pronation is inwards aka marker<vert
        current_vert = np.rad2deg(RS[iteration][0])
        pygame.draw.circle(window, (0, 255, 0), [550, 100], 12, 0)
        print(f"{current_vert}, marker: {marker_vert}")
        if marker_vert < current_vert: # check sup
            check_sup = check_supinate(RS[iteration][0], marker_vert)
            pygame.draw.circle(window, check_sup, [550, 100], 12, 0)

        pygame.draw.circle(window, (0, 255, 0), [550, 70], 12, 0)
        if marker_vert > current_vert: # check pron
            check_pron = check_pronate(RS[iteration][0], marker_vert)
            pygame.draw.circle(window, check_pron, [550, 70], 12, 0)

        pygame.draw.circle(window, (0, 255, 0), [550, 130], 12, 0)        
        overstriding_text = font_a.render(f"Overstriding ", True, (255, 255, 255), (0, 0, 0))
        overstriding_rect = overstriding_text.get_rect()
        overstriding_rect.topright = (535, 110)
        window.blit(overstriding_text, overstriding_rect)
        # check_strike = calc_angle(iteration, 0, "L", 3)
        # pygame.draw.circle(window, check_strike, [550, 130], 12, 0) 

        # adding shoes lol
        shoe_l = pygame.image.load(shoes); shoe_r = pygame.image.load(shoes)
        flipped_shoe_l = pygame.transform.flip(shoe_l, True, False)
        flipped_shoe_r = pygame.transform.flip(shoe_r, True, False)
        shoe_l = pygame.transform.scale(flipped_shoe_l, (40, 50))
        shoe_r = pygame.transform.scale(flipped_shoe_r, (40, 50))
        window.blit(shoe_l, (l_shank_pos[0]-30, l_shank_pos[1]-20)); window.blit(shoe_r, (r_shank_pos[0]-30, r_shank_pos[1]-20))

        # time.sleep(1 / SAMPLING)  # / SAMPLING
        # pygame.display.flip()
        window.blit(window, (0, 0))
        # save image
        filename = "/tmp/snaps/%06d.png" % file_num
        pygame.image.save(window, filename)
        iteration += 1
        window.fill((0, 0, 0))

    pygame.quit()
    # once all photos recorded, create video
    # create name using {DATE}T{TIME}Z.mp4
    # now: datetime = datetime.now()
    # date: str = now.strftime("%Y-%m-%dT%H:%M:%S")
    # video_link: str = f"/tmp/movies/{date}.mp4"
    create_video("/tmp/snaps", video_link)


if __name__ == "__main__":
    data_file_name = sys.argv[1]
    print(data_file_name)
    with open(data_file, "r") as f:
        data = f.read().split("\n")
    ls, lt, rs, rt = read(data)
    create_video_from_file(LS=ls, LT=lt, RS=rs, RT=rt, video_link=data_file_name)
