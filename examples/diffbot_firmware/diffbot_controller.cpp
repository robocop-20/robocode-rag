#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <std_msgs/msg/float64.hpp>

class DiffBotController : public rclcpp::Node {
public:
    DiffBotController() : Node("diffbot_controller"), kp_(1.2), ki_(0.05), kd_(0.01) {
        // Velocity subscriber from teleop or navigation stack
        velocity_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
            "/cmd_vel", 10, std::bind(&DiffBotController::cmd_vel_callback, this, std::placeholders::_1));

        // Odometry publisher
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("/odom", 10);

        // Real-time deterministic control loop timer (50 Hz = 20ms)
        control_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(20), std::bind(&DiffBotController::update_pid_loop, this));
            
        RCLCPP_INFO(this->get_logger(), "DiffBot Controller initialized successfully.");
    }

    void update_pid_loop() {
        double left_error = target_v_left_ - current_v_left_;
        double right_error = target_v_right_ - current_v_right_;

        // PID calculation
        left_effort_ = compute_pid(left_error, left_integral_, left_prev_error_);
        right_effort_ = compute_pid(right_error, right_integral_, right_prev_error_);

        publish_odometry();
    }

private:
    double compute_pid(double error, double& integral, double& prev_error) {
        integral += error * 0.02;
        double derivative = (error - prev_error) / 0.02;
        prev_error = error;
        return (kp_ * error) + (ki_ * integral) + (kd_ * derivative);
    }

    void cmd_vel_callback(const geometry_msgs::msg::Twist::SharedPtr msg) {
        target_v_left_ = msg->linear.x - (msg->angular.z * wheel_base_ / 2.0);
        target_v_right_ = msg->linear.x + (msg->angular.z * wheel_base_ / 2.0);
    }

    void publish_odometry() {
        nav_msgs::msg::Odometry odom;
        odom.header.stamp = this->now();
        odom.header.frame_id = "odom";
        odom.child_frame_id = "base_link";
        odom_pub_->publish(odom);
    }

    double kp_, ki_, kd_;
    double wheel_base_ = 0.35;
    double target_v_left_ = 0.0, target_v_right_ = 0.0;
    double current_v_left_ = 0.0, current_v_right_ = 0.0;
    double left_integral_ = 0.0, left_prev_error_ = 0.0;
    double right_integral_ = 0.0, right_prev_error_ = 0.0;
    double left_effort_ = 0.0, right_effort_ = 0.0;

    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr velocity_sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::TimerBase::SharedPtr control_timer_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<DiffBotController>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
