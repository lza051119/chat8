import hashlib
import math
import random
from PIL import Image
import os

# --- 阶段一: 路径生成算法 ---
# 这是嵌入和提取都会用到的核心公共逻辑
def _generate_path(password: str, width: int, height: int, num_bits: int) -> list[tuple[int, int]]:
    """
    根据给定的密码，为图像生成一个唯一的、伪随机的像素坐标路径。
    每个像素可以存储3个bit（RGB各1位），所以需要的像素数量是 ceil(num_bits / 3)

    Args:
        password (str): 用于生成坐标的密码
        width (int): 图像的像素宽度
        height (int): 图像的像素高度
        num_bits (int): 需要嵌入的总bit数（包括32bit长度头）

    Returns:
        list[tuple[int, int]]: 一个包含 (x, y) 坐标元组的列表，代表嵌入/提取路径。
    """
    # 1. 从密码生成种子
    # 使用 SHA-256 哈希函数处理密码，确保密码的微小变化能导致种子和路径的巨大变化。
    hash_object = hashlib.sha256(password.encode('utf-8'))
    # 用二进制的形式保存这个hash值
    hash_digest = hash_object.digest()
    # 将哈希结果（字节串）转换为一个大整数作为种子
    seed = int.from_bytes(hash_digest, 'big')

    # 2. 初始化伪随机数生成器 (PRNG)
    # 使用相同的种子将确保每次都生成完全相同的随机数序列。
    random.seed(seed)

    # 3. 计算需要的像素数量
    # 每个像素可以存储3个bit（RGB各1位），所以需要的像素数量是 ceil(num_bits / 3)
    num_pixels = math.ceil(num_bits / 3)
    
    # 4. 生成唯一的像素坐标
    # 使用列表来存储坐标，确保顺序的一致性
    path = []
    used_coordinates = set()
    
    # 只要列表内的元素数量不满足要隐藏所有信息所需的像素数，就一直进行循环
    while len(path) < num_pixels:
        # 生成一个在图像范围内的随机坐标
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        coord = (x, y)
        
        # 只有当坐标不重复时才添加到路径中
        if coord not in used_coordinates:
            used_coordinates.add(coord)
            path.append(coord)

    return path

def _message_to_binary(message: str) -> str:
    """将字符串消息转换为二进制字符串。"""
    # 使用UTF-8编码将字符串转换为字节，然后转换为二进制
    utf8_bytes = message.encode('utf-8')
    return ''.join(format(byte, '08b') for byte in utf8_bytes)

def _binary_to_message(binary_data: str) -> str:
    """将二进制字符串转换回原始字符串。"""
    # 每8位切割为一个字节
    byte_chunks = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    # 将每个二进制块转换为整数，再转换为字节
    byte_array = bytes(int(byte, 2) for byte in byte_chunks)
    # 使用UTF-8解码字节数组
    return byte_array.decode('utf-8')


# --- 阶段二: 嵌入过程 ---
def embed(image_path: str, secret_message: str, password: str, output_path: str):
    """
    将秘密信息嵌入到指定的图像中。

    Args:
        image_path (str): 载体图像的路径。
        secret_message (str): 要隐藏的秘密信息。
        password (str): 用于加密路径的密码。
        output_path (str): 保存嵌入信息后图像的路径。
    """
    print("--- 开始嵌入 ---")
    try:
        # 加载图像
        image = Image.open(image_path).convert('RGB')
        width, height = image.width, image.height
        pixels = image.load()
        print(f"成功加载图像: {image_path} (尺寸: {width}x{height})")
    except FileNotFoundError:
        print(f"错误: 图像文件未找到 at '{image_path}'")
        return

    # 1. 准备要嵌入的加密后信息（二进制形式）
    binary_message = _message_to_binary(secret_message)
    message_len = len(binary_message)
    print(f"秘密信息: '{secret_message}'")
    print(f"转换为二进制后长度: {message_len} bits")

    # 2. 隐藏长度
    # 双方需要协商好传输的内容有多少，所以为了方便接头，用固定的32bit去表示此次传输的文件大小是多少，32bit最多是4GB
    binary_len = format(message_len, '032b')

    # 组合要嵌入的所有数据：长度 + 信息
    data_to_embed = binary_len + binary_message
    total_len = len(data_to_embed)
    print(f"元数据(长度)已转换为32位二进制: {binary_len}")
    print(f"总共需要嵌入的数据长度: {total_len} bits")

    # 检查图像容量是否足够
    # 每个像素可以存储3个bit（RGB各1位），所以图像总容量是 width * height * 3 bits
    max_capacity = width * height * 3
    if total_len > max_capacity:
        print(f"错误: 图像容量不足。需要 {total_len} bits，但图像只能容纳 {max_capacity} bits。")
        return

    # 3. 调用路径生成算法，生成嵌入路径
    path = _generate_path(password, width, height, total_len)
    print(f"已根据密码生成 {len(path)} 个像素坐标用于嵌入 {total_len} bits。")

    # 4. & 5. 嵌入长度和数据
    print("正在逐位嵌入数据...")
    for i in range(0, len(data_to_embed), 3):
        # 获取当前像素坐标
        pixel_index = i // 3
        x, y = path[pixel_index]

        # 获取原始像素的RGB值
        r, g, b = pixels[x, y]

        # 获取要嵌入的3个bit（如果不足3个bit，用0补齐）
        bit_r = data_to_embed[i] if i < len(data_to_embed) else '0'
        bit_g = data_to_embed[i + 1] if i + 1 < len(data_to_embed) else '0'
        bit_b = data_to_embed[i + 2] if i + 2 < len(data_to_embed) else '0'

        # 使用 LSB (最低有效位) 技术修改RGB三个通道
        # 修改红色通道
        if bit_r == '1':
            r = r | 1
        else:
            r = r & ~1
        
        # 修改绿色通道
        if bit_g == '1':
            g = g | 1
        else:
            g = g & ~1
            
        # 修改蓝色通道
        if bit_b == '1':
            b = b | 1
        else:
            b = b & ~1

        # 将修改后的像素写回
        pixels[x, y] = (r, g, b)

    # 6. 保存修改后的图片
    image.save(output_path)
    print(f"--- 嵌入完成！已保存至: {output_path} ---")


# --- 阶段三: 提取过程 ---
def extract(image_path: str, password: str) -> str | None:
    """
    从图像中提取隐藏的信息。

    Args:
        image_path (str): 含有隐藏信息的图像路径。
        password (str): 用于解密路径的密码。

    Returns:
        str | None: 如果成功，则返回提取出的秘密信息；否则返回 None。
    """
    print("\n--- 开始提取过程 ---")
    try:
        image = Image.open(image_path).convert('RGB')
        width, height = image.width, image.height
        pixels = image.load()
        print(f"成功加载图像: {image_path} (尺寸: {width}x{height})")
    except FileNotFoundError:
        print(f"错误: 图像文件未找到 at '{image_path}'")
        return None

    # 1. & 2. 获取密码，并生成用于提取长度的路径
    # 首先只需要前32个bit来获取信息长度，需要 ceil(32/3) = 11 个像素
    pixels_for_len = math.ceil(32 / 3)
    path_for_len = _generate_path(password, width, height, 32)
    print(f"已根据密码生成前 {len(path_for_len)} 个像素坐标，用于提取32bit长度信息。")

    # 3. 提取长度
    binary_len = ""
    for i in range(pixels_for_len):
        x, y = path_for_len[i]
        r, g, b = pixels[x, y]
        
        # 读取RGB三个通道的最低有效位
        bit_r = str(r & 1)
        bit_g = str(g & 1)
        bit_b = str(b & 1)
        
        # 按顺序添加bit，但不能超过32位
        if len(binary_len) < 32:
            binary_len += bit_r
        if len(binary_len) < 32:
            binary_len += bit_g
        if len(binary_len) < 32:
            binary_len += bit_b

    # 将32位二进制长度转换为整数
    message_len = int(binary_len, 2)
    print(f"提取到的二进制长度: {binary_len}")
    print(f"解析出的信息长度为: {message_len} bits")

    # 4. 检查提取的长度是否合理
    total_bits = 32 + message_len
    max_capacity = width * height * 3
    if total_bits > max_capacity:
        print(f"错误: 提取出的信息长度超出了图像容量。需要 {total_bits} bits，但图像只能容纳 {max_capacity} bits。很可能密码错误或文件已损坏。")
        return None

    # 生成完整路径（包含长度和数据部分）
    full_path = _generate_path(password, width, height, total_bits)

    # 5. 提取数据
    print("正在提取秘密信息...")
    binary_message = ""
    
    # 计算需要跳过的bit数（前32个bit是长度信息）
    bits_extracted = 0
    for i in range(len(full_path)):
        x, y = full_path[i]
        r, g, b = pixels[x, y]
        
        # 读取RGB三个通道的最低有效位
        bit_r = str(r & 1)
        bit_g = str(g & 1)
        bit_b = str(b & 1)
        
        # 跳过前32个bit（长度信息），只提取消息内容
        if bits_extracted >= 32 and len(binary_message) < message_len:
            binary_message += bit_r
        if bits_extracted + 1 >= 32 and len(binary_message) < message_len:
            binary_message += bit_g
        if bits_extracted + 2 >= 32 and len(binary_message) < message_len:
            binary_message += bit_b
            
        bits_extracted += 3
        
        # 如果已经提取完所有消息bit，就退出循环
        if len(binary_message) >= message_len:
            break

    # 6. 将提取的二进制数据转换回原始信息
    try:
        secret_message = _binary_to_message(binary_message)
        print("--- 提取完成！---")
        return secret_message
    except Exception as e:
        print(f"错误: 无法将提取的二进制数据转换为文本。很可能密码错误。({e})")
        return None