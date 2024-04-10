import os
from typing import Final

import pygame
import numpy as np
import moviepy.video.io.ImageSequenceClip

# global variables
LS = []
LT = []
RS = []
RT = []
SCREEN_W = 600
SCREEN_H = 600
X_CENTER = SCREEN_W * 0.5
Y_CENTER = SCREEN_H * 0.5
LEG_LENGTH = 100
SAMPLING = 15

ROTATE = 1.5708

data_file = "data.run"


def reading():
    file = open(data_file, "r")
    file.readline()
    file.readline()
    for line in file:
        temp = line.split(",")
        LS.append([float(temp[0]), float(temp[1]), float(temp[2])])
        LT.append([float(temp[3]), float(temp[4]), float(temp[5])])
        RS.append([float(temp[6]), float(temp[7]), float(temp[8])])
        RT.append([float(temp[9]), float(temp[10]), float(temp[11])])

    file.close()


def get_knee_pos(iteration: float, leg: str, point: str):

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


def get_shank_pos(it: float, knee_pos: list[float], leg: str):
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


def create_video(image_folder: str, video_name: str):
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
    clip.write_videofile(video_name)
    print("video released!")


def main():
    reading()

    try:
        os.makedirs("/tmp/snaps")
    except OSError:
        pass

    try:
        os.makedirs("/tmp/movies")
    except OSError:
        pass

    pygame.init()
    pygame.display.init()
    window = pygame.display.set_mode((SCREEN_W, SCREEN_W))
    pygame.display.set_caption("2D Animation - Lateral Perspective")
    window.fill((0, 0, 0))

    # displaying text
    font_a = pygame.font.SysFont("Arial", 40)
    font_b = pygame.font.SysFont("Arial", 24)

    # initialize top of thigh position at center of screen
    l_thigh_pos = [X_CENTER, Y_CENTER]
    r_thigh_pos = [X_CENTER, Y_CENTER]

    cadence = []
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
        # left and right knee pos
        l_knee_pos = get_knee_pos(iteration, "L", "K")
        print(l_knee_pos)
        r_knee_pos = get_knee_pos(iteration, "R", "K")

        # # left and right shank pos
        l_shank_pos = get_shank_pos(iteration, l_knee_pos, "L")
        print(l_shank_pos)
        r_shank_pos = get_shank_pos(iteration, r_knee_pos, "R")

        # displaying knee angles of respective legs
        left = "Left: "
        left_text = font_a.render(left, True, (0, 0, 255), (255, 0, 0))
        # print(f"LT: {LT[iteration][1]}, LS: {LS[iteration][1]}")
        l_angle = str(
            round(abs(LT[iteration][1] - LS[iteration][1]) % 180 * 180 / np.pi, 2)
        )
        l_angle_text = font_a.render(l_angle, True, (255, 255, 255), (0, 0, 0))

        right = "Right: "
        right_text = font_a.render(right, True, (128, 0, 128), (0, 255, 0))
        r_angle = str(
            round(abs(RS[iteration][1] - RT[iteration][1]) % 180 * 180 / np.pi, 2)
        )
        r_angle_text = font_a.render(r_angle, True, (255, 255, 255), (0, 0, 0))

        window.blit(left_text, (50, 100))
        window.blit(l_angle_text, (140, 100))
        window.blit(right_text, (50, 150))
        window.blit(r_angle_text, (160, 150))

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

        transfer_x = LEG_LENGTH * np.cos(LT[iteration][2] + ROTATE)
        transfer_x2 = LEG_LENGTH * np.cos(LT[iteration + 1][2] + ROTATE)
        if (X_CENTER + transfer_x) > X_CENTER and (X_CENTER + transfer_x2) < X_CENTER:
            cadence += [iteration / SAMPLING]
            if len(cadence) > 1:
                multiplier = 1 / ((cadence[-1] - cadence[0]) / 60)
                spm = round(len(cadence) * multiplier, 2)
            elif len(cadence) > 60:
                pass
            # print(cadence, spm)
        spm_text = font_b.render(
            f"Cadence: {spm} spm", True, (255, 255, 255), (0, 0, 0)
        )
        window.blit(spm_text, (50, 80))

        # adding shoes lol
        # shoe_l = pygame.image.load(shoes); shoe_r = pygame.image.load(shoes)
        # shoe_l = pygame.transform.scale(shoe_l, (40, 50)); shoe_r = pygame.transform.scale(shoe_r, (40, 50))
        # window.blit(shoe_l, (l_shank_pos[0]-30, l_shank_pos[1]-20)); window.blit(shoe_r, (r_shank_pos[0]-30, r_shank_pos[1]-20))

        # displaying length of activity
        activity = "Length of activity: " + str(round(iteration / SAMPLING, 2))
        activity_length = font_b.render(activity, True, (255, 255, 255), (0, 0, 0))
        window.blit(activity_length, (50, 50))

        # time.sleep(1 / SAMPLING)  # / SAMPLING
        pygame.display.flip()
        # save image
        filename = "/tmp/snaps/%06d.png" % file_num
        pygame.image.save(window, filename)
        iteration += 1
        window.fill((0, 0, 0))

    pygame.quit()
    # once all photos recorded, create video
    create_video("/tmp/snaps", "/tmp/movies/output.mp4")


if __name__ == "__main__":
    main()
