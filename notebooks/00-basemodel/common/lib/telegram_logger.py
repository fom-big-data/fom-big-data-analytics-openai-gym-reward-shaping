import glob
import os

import numpy as np
import telegram_send


class TelegramLogger:

    def log_parameters(run_name, output_directory, conf_directory, environment_id, batch_size, gamma, eps_start,
                       eps_end, eps_decay, num_atoms, vmin, vmax, target_update_rate, model_save_rate,
                       replay_memory_size, num_frames,
                       reward_pong_player_racket_hits_ball,
                       reward_pong_player_racket_covers_ball,
                       reward_pong_player_racket_close_to_ball_linear,
                       reward_pong_player_racket_close_to_ball_quadratic,
                       reward_pong_opponent_racket_hits_ball,
                       reward_pong_opponent_racket_covers_ball,
                       reward_pong_opponent_racket_close_to_ball_linear,
                       reward_pong_opponent_racket_close_to_ball_quadratic,
                       reward_breakout_player_racket_hits_ball,
                       reward_breakout_player_racket_covers_ball,
                       reward_breakout_player_racket_close_to_ball_linear,
                       reward_breakout_player_racket_close_to_ball_quadratic,
                       reward_spaceinvaders_player_avoids_line_of_fire,
                       reward_freeway_chicken_vertical_position,
                       reward_potential_based):
        telegram_line = "<b>run " + run_name + "</b>" \
                        + "\n" \
                        + "\nenvironment id " + str(environment_id) \
                        + "\nbatch size " + str(batch_size) \
                        + "\ngamma " + str(gamma) \
                        + "\neps start " + str(eps_start) \
                        + "\neps end " + str(eps_end) \
                        + "\neps decay " + str(eps_decay) \
                        + "\nnum atoms " + str(num_atoms) \
                        + "\nvmin " + str(vmin) \
                        + "\nvmax " + str(vmax) \
                        + "\ntarget update rate " + str(target_update_rate) \
                        + "\nsave model rate " + str(model_save_rate) \
                        + "\nreplay memory size " + str(replay_memory_size) \
                        + "\nnum frames " + str(num_frames) \
                        + "\n" \
                        + TelegramLogger.build_reward_parameter("player racket hits ball",
                                                                reward_pong_player_racket_hits_ball) \
                        + TelegramLogger.build_reward_parameter("player racket covers ball",
                                                                reward_pong_player_racket_covers_ball) \
                        + TelegramLogger.build_reward_parameter("player racket close to ball linear",
                                                                reward_pong_player_racket_close_to_ball_linear) \
                        + TelegramLogger.build_reward_parameter("player racket close to ball quadratic",
                                                                reward_pong_player_racket_close_to_ball_quadratic) \
                        + TelegramLogger.build_reward_parameter("opponent racket hits ball",
                                                                reward_pong_opponent_racket_hits_ball) \
                        + TelegramLogger.build_reward_parameter("opponent racket covers ball",
                                                                reward_pong_opponent_racket_covers_ball) \
                        + TelegramLogger.build_reward_parameter("opponent racket close to ball linear",
                                                                reward_pong_opponent_racket_close_to_ball_linear) \
                        + TelegramLogger.build_reward_parameter("opponent racket close to ball quadratic",
                                                                reward_pong_opponent_racket_close_to_ball_quadratic) \
                        + TelegramLogger.build_reward_parameter("player racket hits ball",
                                                                reward_breakout_player_racket_hits_ball) \
                        + TelegramLogger.build_reward_parameter("player racket covers ball",
                                                                reward_breakout_player_racket_covers_ball) \
                        + TelegramLogger.build_reward_parameter("player racket close to ball linear",
                                                                reward_breakout_player_racket_close_to_ball_linear) \
                        + TelegramLogger.build_reward_parameter("player racket close to ball quadratic",
                                                                reward_breakout_player_racket_close_to_ball_quadratic) \
                        + TelegramLogger.build_reward_parameter("player avoids line of fire",
                                                                reward_spaceinvaders_player_avoids_line_of_fire) \
                        + TelegramLogger.build_reward_parameter("chicken vertical position",
                                                                reward_freeway_chicken_vertical_position) \
                        + TelegramLogger.build_reward_parameter("potential based", reward_potential_based)

        # Get config path
        list_of_configs = glob.glob(conf_directory + "/" + "telegram.config")
        config_path = max(list_of_configs, key=os.path.getctime)

        # Send line to telegram
        telegram_send.send(messages=[telegram_line], parse_mode="html", conf=config_path)

    def build_reward_parameter(name, value):
        return "\n" + str(name) + "=" + str(value) if value != 0.0 else ""

    def log_episode(run_name, output_directory, conf_directory, max_frames, total_episodes, total_frames,
                    total_duration, total_original_rewards, total_shaped_rewards, episode_frames,
                    episode_original_reward, episode_shaped_reward, episode_loss, episode_duration):
        avg_original_reward_per_episode = np.mean(total_original_rewards[-50:])
        avg_shaped_reward_per_episode = np.mean(total_shaped_rewards[-50:])

        # Assemble line
        telegram_line = "<b>run " + run_name + "</b>\n" \
                        + "\nframes {:8d}".format(total_frames) + "/" + str(max_frames) \
                        + "\nepisode {:5d}".format(total_episodes) \
                        + "\nepisode reward " + str(round(episode_original_reward, 2)) \
                        + " / shaped " + str(round(episode_shaped_reward, 2)) \
                        + "\naverage reward " + str(round(avg_original_reward_per_episode, 2)) \
                        + " / shaped " + str(round(avg_shaped_reward_per_episode, 2)) \
                        + "\nloss " + str(round(episode_loss, 4)) \
 \
            # Get animation path
        list_of_files = glob.glob(output_directory + "/" + "*.gif")
        gif_path = max(list_of_files, key=os.path.getctime)
        # Get config path
        list_of_configs = glob.glob(conf_directory + "/" + "telegram.config")
        config_path = max(list_of_configs, key=os.path.getctime)

        # Send line to telegram
        with open(gif_path, "rb") as f:
            telegram_send.send(messages=[telegram_line], animations=[f], parse_mode="html", conf=config_path)